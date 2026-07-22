"""Authored deep manifest for Class 5 English Chapter 5.

The embedded baseline preserves the original Zidd-authored chapter manifest.
The bounded repair layer below only strengthens learner-visible authority,
atomic grading evidence, and transfer/review depth.
"""

from __future__ import annotations

import json
import re
from typing import Any


MANIFEST = json.loads(r'''{
  "schema_version": "school-class5-deep-manifest-v1",
  "chapter": {
    "chapter_id": "eng_c5_ch05",
    "chapter_no": 5,
    "title": "The Frog",
    "book_title": "Santoor",
    "unit_title": "Water",
    "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf",
    "source_note": "NCERT structural alignment only. All teaching passages, prompts, examples, answers, and rubrics are original Zidd-authored content and do not copy the textbook body.",
    "content_version": "2026-07-15.5",
    "certification_version": "2026-07-15.5",
    "authorship": {
      "zidd_authored_original": true,
      "textbook_body_or_questions_copied": false,
      "source_analysis_reference": "agent-reviewed official structural exercise matrix for eng_c5_ch05"
    }
  },
  "source_anchors": [
    {
      "anchor_id": "eng_c5_ch05:recite:1",
      "section_label": "Let us Recite",
      "page_start": 1,
      "page_end": 1,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf#page=1",
      "coverage_treatment": "guided_only",
      "required_for_chapter_certification": false
    },
    {
      "anchor_id": "eng_c5_ch05:think:2",
      "section_label": "Let us Think",
      "page_start": 2,
      "page_end": 2,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf#page=2",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch05:learn:3-4",
      "section_label": "Let us Learn",
      "page_start": 3,
      "page_end": 4,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf#page=3",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch05:speak:4-5",
      "section_label": "Let us Speak",
      "page_start": 4,
      "page_end": 5,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf#page=4",
      "coverage_treatment": "textbook_companion",
      "required_for_chapter_certification": false
    },
    {
      "anchor_id": "eng_c5_ch05:listen:5-6",
      "section_label": "Let us Listen",
      "page_start": 5,
      "page_end": 6,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf#page=5",
      "coverage_treatment": "offline_group_activity",
      "required_for_chapter_certification": false
    },
    {
      "anchor_id": "eng_c5_ch05:write:7",
      "section_label": "Let us Write",
      "page_start": 7,
      "page_end": 7,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf#page=7",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch05:do:8-9",
      "section_label": "Let us Do",
      "page_start": 8,
      "page_end": 9,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf#page=8",
      "coverage_treatment": "textbook_companion",
      "required_for_chapter_certification": false
    },
    {
      "anchor_id": "eng_c5_ch05:explore:10",
      "section_label": "Let us Explore",
      "page_start": 10,
      "page_end": 10,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa105.pdf#page=10",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    }
  ],
  "levels": [
    {
      "level_id": "frog_poem_meaning",
      "title": "Read the frog poem as a poem",
      "focus": "interpret poetic description without treating exaggeration as science",
      "outcome": "Use the poem's words to identify stated frog details and explain when a line creates an imaginative picture rather than a literal scientific claim.",
      "skill_ids": [
        "reading.poetic_language",
        "reading.sentence_comprehension"
      ],
      "episode_kind": "meaning_encounter",
      "source_anchor_ids": [
        "eng_c5_ch05:think:2"
      ],
      "companion_source_anchor_ids": [
        "eng_c5_ch05:recite:1"
      ],
      "connect": {
        "teaching_block": "A poem can include accurate observations and playful exaggeration; careful readers use the line's purpose before treating it as factual information.",
        "passage": "A poem says a frog 'leaps towards the moon.' The image creates excitement, but it does not claim that an ordinary frog reaches the moon.",
        "prompt": "Continue when you can explain how this example helps you interpret poetic description without treating exaggeration as science."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "frog_poem_meaning:co_construct",
        "teaching_block": "Use the poem's wording and decide whether the line states a detail, creates an image, or exaggerates for effect. Locate the exact clue before comparing the choices.",
        "passage": "The poem speaker rests near ponds, rain, and a muddy drain.",
        "prompt": "Which setting is directly supported?",
        "skill_ids": [
          "reading.poetic_language",
          "reading.sentence_comprehension"
        ],
        "options": [
          "a dry mountain cave",
          "damp places near water",
          "a desert at noon",
          "a frozen roof"
        ],
        "accepted_answers": [
          "damp places near water"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:guided:1",
          "teaching_block": "Use the poem's wording and decide whether the line states a detail, creates an image, or exaggerates for effect. Read the whole sentence, then test every option against its meaning.",
          "passage": "The speaker says its colours match plants and leaves.",
          "prompt": "What picture does this line create?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the frog blends with its surroundings",
            "the frog paints the plants",
            "the leaves copy the frog",
            "the frog becomes invisible everywhere"
          ],
          "accepted_answers": [
            "the frog blends with its surroundings"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:guided:2",
          "teaching_block": "Use the poem's wording and decide whether the line states a detail, creates an image, or exaggerates for effect. Track who or what each detail belongs to before deciding.",
          "passage": "The poem says the frog jumps 'up into the sky.'",
          "prompt": "How should this line be read?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "as proof that frogs can fly",
            "as playful exaggeration of a high jump",
            "as a weather report",
            "as a rule about every animal"
          ],
          "accepted_answers": [
            "as playful exaggeration of a high jump"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:guided:3",
          "teaching_block": "Identify the shared visual feature and keep the comparison separate from literal fact.",
          "passage": "A poem calls the pond a green mirror that trembles whenever a frog lands.",
          "prompt": "Which explanation respects the poetic image?",
          "skill_ids": [
            "reading.poetic_language"
          ],
          "options": [
            "A glass mirror is hidden under every pond.",
            "The still green surface reflects light like a mirror, then ripples when the frog lands.",
            "The frog paints the entire pond green.",
            "The pond stops holding water when it trembles."
          ],
          "accepted_answers": [
            "The still green surface reflects light like a mirror, then ripples when the frog lands."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:guided:4",
          "teaching_block": "Translate the image into a plausible scene by using colour, light, position, and movement clues.",
          "passage": "The poet writes, 'Night stitched silver dots across the marsh.'",
          "prompt": "What scene does the line most likely create?",
          "skill_ids": [
            "reading.poetic_language"
          ],
          "options": [
            "Someone used a needle to sew the marsh shut.",
            "The marsh became a silver metal sheet.",
            "Moonlight or fireflies appear as small bright points across the dark marsh.",
            "Every frog carried a sewing kit at night."
          ],
          "accepted_answers": [
            "Moonlight or fireflies appear as small bright points across the dark marsh."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:independent:1",
          "teaching_block": "Explain the poetic image and separate its imaginative effect from a literal scientific claim. Build the answer from two visible pieces of evidence.",
          "passage": "A poem says, 'I spring so high the clouds look near.'",
          "prompt": "Explain the image and state what should not be treated as literal fact.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "image",
              "description": "Explains that the line makes the jump feel very high or exciting.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "not_literal",
              "description": "States that the frog does not literally reach clouds.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "image",
              "description": "Explains that the line makes the jump feel very high or exciting.",
              "any_of": [
                "jump feels very high",
                "creates an exciting high-jump image"
              ]
            },
            {
              "id": "not_literal",
              "description": "States that the frog does not literally reach clouds.",
              "any_of": [
                "does not reach clouds",
                "not a scientific height claim"
              ]
            }
          ],
          "forbidden_phrases": [
            "frogs reach clouds",
            "frog can fly"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "jump",
            "feels",
            "very",
            "high",
            "creates"
          ],
          "model_answer": "The line creates an exciting image of a very high jump, but it does not literally claim that a frog can reach the clouds. Reference evidence states: jump feels very high; does not reach clouds.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:independent:2",
          "teaching_block": "Explain the poetic image and separate its imaginative effect from a literal scientific claim. State the relationship and support it with the relevant detail.",
          "passage": "The poem speaker calls its croak a song and describes the pond proudly.",
          "prompt": "What mood do these choices create, and which words support it?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "mood",
              "description": "Identifies pride, joy, or confidence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Uses song or proud pond language as evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "mood",
              "description": "Identifies pride, joy, or confidence.",
              "any_of": [
                "proud",
                "joyful",
                "confident"
              ]
            },
            {
              "id": "evidence",
              "description": "Uses song or proud pond language as evidence.",
              "any_of": [
                "calls the croak a song",
                "feels proud in the pond"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "proud",
            "joyful",
            "confident",
            "calls",
            "croak"
          ],
          "model_answer": "Calling the croak a song and describing pride in the pond creates a joyful, confident mood. Reference evidence states: calls the croak a song.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:independent:3",
          "teaching_block": "Name the compared things, explain the shared function, and then draw the literal boundary explicitly.",
          "passage": "In the poem, reeds become tall green curtains and a frog slips behind them when footsteps approach.",
          "prompt": "Explain the curtain image and state what it does not mean literally.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "image",
              "description": "Explains the reeds as a screen that hides the frog.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "Rejects literal cloth curtains in the pond.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "image",
              "description": "Explains the reeds as a screen that hides the frog.",
              "any_of": [
                "reeds resemble green curtains"
              ]
            },
            {
              "id": "boundary",
              "description": "Rejects literal cloth curtains in the pond.",
              "any_of": [
                "does not mean that cloth curtains hang"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "poem",
            "reeds",
            "become",
            "tall",
            "green",
            "curtains",
            "frog",
            "slips"
          ],
          "model_answer": "The upright reeds resemble green curtains because they form a screen that hides the frog. The poem does not mean that cloth curtains hang in the pond.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:independent:4",
          "teaching_block": "Use both the sound quality and its apparent travel; avoid claiming that a physical drum is present.",
          "passage": "A verse says the frog's call rolls like a tiny drumbeat from leaf to leaf after rain.",
          "prompt": "Interpret the comparison using sound and movement clues from the line.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "sound",
              "description": "Connects the repeated call with a drumbeat.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "movement",
              "description": "Explains that the sound seems to travel across leaves.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sound",
              "description": "Connects the repeated call with a drumbeat.",
              "any_of": [
                "call is compared with a tiny drumbeat"
              ]
            },
            {
              "id": "movement",
              "description": "Explains that the sound seems to travel across leaves.",
              "any_of": [
                "seems to travel across the wet leaves"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "verse",
            "says",
            "frog's",
            "call",
            "rolls",
            "like",
            "tiny",
            "drumbeat"
          ],
          "model_answer": "The frog's repeated call is compared with a tiny drumbeat because both have a steady sound that seems to travel across the wet leaves.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:transfer:1",
          "teaching_block": "Explain the poetic image and separate its imaginative effect from a literal scientific claim. Explain the first part before connecting it to the result.",
          "passage": "A verse says a turtle 'carries its little house wherever it goes.'",
          "prompt": "Explain the comparison without treating the shell as a built house.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "comparison",
              "description": "Connects the shell with protection like a house.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "States that the shell is not literally a built house.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "comparison",
              "description": "Connects the shell with protection like a house.",
              "any_of": [
                "shell protects like a house",
                "portable shelter image"
              ]
            },
            {
              "id": "boundary",
              "description": "States that the shell is not literally a built house.",
              "any_of": [
                "not a built house",
                "poetic comparison"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 17,
          "relevance_terms": [
            "shell",
            "protects",
            "like",
            "house",
            "portable"
          ],
          "model_answer": "The verse compares the turtle's shell to a portable house because it protects the animal, but the shell is not literally a built house. Reference evidence states: shell protects like a house; not a built house.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:transfer:2",
          "teaching_block": "Explain the poetic image and separate its imaginative effect from a literal scientific claim. Use your own words while preserving every required idea.",
          "passage": "The lines say a frog hides among green leaves and a hunter passes without noticing it.",
          "prompt": "Explain the supported relationship in the image.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "match",
              "description": "States that the frog's appearance matches the leaves.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Explains that the match makes it harder to notice.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "match",
              "description": "States that the frog's appearance matches the leaves.",
              "any_of": [
                "matches the leaves",
                "blends with green leaves"
              ]
            },
            {
              "id": "result",
              "description": "Explains that the match makes it harder to notice.",
              "any_of": [
                "harder to notice",
                "hunter passes without seeing"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "matches",
            "leaves",
            "blends",
            "with",
            "green"
          ],
          "model_answer": "The frog blends with the green leaves, making it harder for the hunter to notice it. Reference evidence states: matches the leaves; harder to notice.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:transfer:3",
          "teaching_block": "Transfer figurative interpretation to a new animal sound by connecting the image to one shared quality and one nonliteral limit.",
          "passage": "A new poem says, 'The cricket wound a thin thread of music around the sleeping garden.'",
          "prompt": "Explain the image and identify one literal boundary.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "comparison",
              "description": "Explains the call as a thin musical thread.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "States that no real thread surrounds the plants.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "comparison",
              "description": "Explains the call as a thin musical thread.",
              "any_of": [
                "call is imagined as a thin thread"
              ]
            },
            {
              "id": "boundary",
              "description": "States that no real thread surrounds the plants.",
              "any_of": [
                "no real thread is wrapped"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "poem",
            "says",
            "'the",
            "cricket",
            "wound",
            "thin",
            "thread",
            "music"
          ],
          "model_answer": "The cricket's continuous high call is imagined as a thin thread surrounding the quiet garden. No real thread is wrapped around the plants.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:transfer:4",
          "teaching_block": "Explain the real detail beneath a poetic image and mark the boundary between comparison and literal fact. Apply the same construct to this new passage. Use the visible passage to practise poetic language and sentence comprehension; include both details.",
          "passage": "A poem says, 'Fireflies buttoned the dark field with tiny lamps,' while the next line describes insects blinking above the grass.",
          "prompt": "Explain the buttoned-field image and identify the literal action given by the next line.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_poem_meaning:transfer:4:image",
              "description": "Explains the shared small bright points across darkness.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_poem_meaning:transfer:4:literal",
              "description": "States the real flashing action and rejects sewing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_poem_meaning:transfer:4:image",
              "description": "Explains the shared small bright points across darkness.",
              "any_of": [
                "tiny bright buttons",
                "across a dark field"
              ]
            },
            {
              "id": "frog_poem_meaning:transfer:4:literal",
              "description": "States the real flashing action and rejects sewing.",
              "any_of": [
                "insects flash their lights",
                "not that they sew real buttons"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "blinking",
            "fireflies",
            "bright"
          ],
          "model_answer": "The blinking fireflies look like tiny bright buttons spread across a dark field. The literal action is that the insects flash their lights above the grass, not that they sew real buttons.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:review:1",
          "teaching_block": "Explain the poetic image and separate its imaginative effect from a literal scientific claim. Apply the same reasoning to a different setting and justify it.",
          "passage": "A poem says a dragonfly 'stitches the air with silver wings.'",
          "prompt": "Interpret the line as imagery and name the actual action underneath it.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "imagery",
              "description": "Explains that the movement is compared with stitching a path.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Identifies flying as the actual action.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "imagery",
              "description": "Explains that the movement is compared with stitching a path.",
              "any_of": [
                "movement compared to stitching",
                "creates a silver trail image"
              ]
            },
            {
              "id": "action",
              "description": "Identifies flying as the actual action.",
              "any_of": [
                "dragonfly is flying",
                "wings move through air"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "movement",
            "compared",
            "stitching",
            "creates",
            "silver"
          ],
          "model_answer": "The line imagines the dragonfly's silver wings stitching a path through the air; the actual action is rapid flight. Reference evidence states: movement compared to stitching; dragonfly is flying.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:review:2",
          "teaching_block": "Explain the poetic image and separate its imaginative effect from a literal scientific claim. Separate what is stated from what can reasonably be inferred.",
          "passage": "The frog poem combines damp settings, quick tongue movement, hiding colours, and webbed feet.",
          "prompt": "Choose two details and explain how each contributes to the poem's picture of frog life.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "detail_one",
              "description": "Uses one accurate poem detail and its contribution.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "detail_two",
              "description": "Uses a second different detail and its contribution.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "detail_one",
              "description": "Uses one accurate poem detail and its contribution.",
              "any_of": [
                "damp setting",
                "quick tongue catches food",
                "hiding colours"
              ]
            },
            {
              "id": "detail_two",
              "description": "Uses a second different detail and its contribution.",
              "any_of": [
                "webbed feet support swimming",
                "croak creates sound",
                "snakes create danger"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "damp",
            "setting",
            "quick",
            "tongue",
            "catches"
          ],
          "model_answer": "The damp setting places the frog near water, while its webbed feet create a picture of easy swimming. Reference evidence states: webbed feet support swimming.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:review:3",
          "teaching_block": "Explain the real detail beneath a poetic image and mark the boundary between comparison and literal fact. Retrieve the construct, then verify it against the passage. Use the visible passage to practise poetic language and sentence comprehension; include both details.",
          "passage": "A verse calls a gecko's feet 'tiny anchors on the wall' and then says the animal stays firm on smooth stone.",
          "prompt": "Interpret anchors using the stated action and mark the nonliteral boundary.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_poem_meaning:review:3:meaning",
              "description": "Links the anchor image to staying firm.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_poem_meaning:review:3:boundary",
              "description": "States that the feet are not literal metal anchors.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_poem_meaning:review:3:meaning",
              "description": "Links the anchor image to staying firm.",
              "any_of": [
                "compared with tiny anchors",
                "help it stay firm"
              ]
            },
            {
              "id": "frog_poem_meaning:review:3:boundary",
              "description": "States that the feet are not literal metal anchors.",
              "any_of": [
                "not metal anchors",
                "gripping feet"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "gecko's",
            "compared",
            "anchors"
          ],
          "model_answer": "The gecko's feet are compared with tiny anchors because they help it stay firm on the wall. They are gripping feet, not metal anchors fixed into stone.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "frog_poem_meaning:review:4",
          "teaching_block": "Explain the real detail beneath a poetic image and mark the boundary between comparison and literal fact. Retrieve the construct, then verify it against the passage. Use the visible passage to practise poetic language and sentence comprehension; include both details.",
          "passage": "The poem says a snail 'writes a silver line across the path.' The next sentence states that a shiny trail remains behind its moving body.",
          "prompt": "Explain the writing image using the sentence clue and state what is actually left.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_poem_meaning:review:4:comparison",
              "description": "Explains how movement creates a writing-like line.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_poem_meaning:review:4:fact",
              "description": "Identifies the trail and rejects literal writing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_poem_meaning:review:4:comparison",
              "description": "Explains how movement creates a writing-like line.",
              "any_of": [
                "seems to write",
                "leaves a narrow shiny line"
              ]
            },
            {
              "id": "frog_poem_meaning:review:4:fact",
              "description": "Identifies the trail and rejects literal writing.",
              "any_of": [
                "silver-looking trail",
                "not pencil marks or words"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "moving",
            "snail",
            "seems"
          ],
          "model_answer": "The moving snail seems to write because its route leaves a narrow shiny line. What actually remains is a silver-looking trail, not pencil marks or words.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "poetic-line-treated-as-science",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "misconception": "The learner treats playful exaggeration or imagery as a literal biological fact, or ignores the exact words that create the image.",
          "remediation": "Mark the observable detail and the imaginative wording separately, then rewrite the line once as imagery and once as a cautious factual statement.",
          "support_check_ids": [
            "frog_poem_meaning:support:bridge",
            "frog_poem_meaning:support:masterclass",
            "frog_poem_meaning:support:revision_level_1",
            "frog_poem_meaning:support:revision_level_2",
            "frog_poem_meaning:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:support:bridge",
          "teaching_block": "Use the poem's wording and decide whether the line states a detail, creates an image, or exaggerates for effect. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "The frog warns that snakes are near.",
          "prompt": "Which feeling does the warning add?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "complete relaxation",
            "alertness to danger",
            "pride in a prize",
            "confusion about rain"
          ],
          "accepted_answers": [
            "alertness to danger"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:support:masterclass",
          "teaching_block": "Use the poem's wording and decide whether the line states a detail, creates an image, or exaggerates for effect. Reject any option that adds a fact the passage never gives.",
          "passage": "The speaker describes loud croaks as songs.",
          "prompt": "What poetic move is being used?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the call is presented as music",
            "the frog writes a textbook",
            "the pond becomes silent",
            "the snake sings instead"
          ],
          "accepted_answers": [
            "the call is presented as music"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:support:revision_level_1",
          "teaching_block": "Use the poem's wording and decide whether the line states a detail, creates an image, or exaggerates for effect. Break the task into one smaller decision and check it carefully.",
          "passage": "The line about webbed feet follows a line about swimming with ease.",
          "prompt": "Which relationship is suggested?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the feet support swimming",
            "the feet stop all movement",
            "the pond creates the feet",
            "the frog uses wings underwater"
          ],
          "accepted_answers": [
            "the feet support swimming"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:support:revision_level_2",
          "teaching_block": "Use the poem's wording and decide whether the line states a detail, creates an image, or exaggerates for effect. Name the rule first, then apply it to this new example.",
          "passage": "The poem mentions a fast tongue and food in neighbouring lines.",
          "prompt": "Which action is stated?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the tongue catches food",
            "the tongue builds a nest",
            "the tongue changes the weather",
            "the food catches the frog"
          ],
          "accepted_answers": [
            "the tongue catches food"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "frog_poem_meaning:support:revision_level_3",
          "teaching_block": "Use the poem's wording and decide whether the line states a detail, creates an image, or exaggerates for effect. Compare the tempting error with the evidence that corrects it.",
          "passage": "The repeated first-person voice says 'I' throughout the poem.",
          "prompt": "Who is the imagined speaker?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "a frog",
            "a fish",
            "a snake",
            "a scuba diver"
          ],
          "accepted_answers": [
            "a frog"
          ]
        }
      }
    },
    {
      "level_id": "frog_life_stage_and_words",
      "title": "Order frog life stages and use context",
      "focus": "sequence supplied stages and infer biological words",
      "outcome": "Place supplied frog life-stage events in order and infer a stage word from context without adding unsupported scientific detail.",
      "skill_ids": [
        "reading.event_sequence",
        "reading.word_meaning_context"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch05:think:2"
      ],
      "connect": {
        "teaching_block": "A life-stage sequence depends on clear before-and-after clues; context words such as tail and newly hatched help explain an unfamiliar stage name.",
        "passage": "A supplied chart shows eggs hatching into tailed swimmers, legs appearing later, and an adult frog leaving the water edge. The order comes from the chart, not from a guess.",
        "prompt": "Continue when you can explain how this example helps you sequence supplied stages and infer biological words."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "frog_life_stage_and_words:co_construct",
        "teaching_block": "Use the stated stage features and transition clues to choose the next event or contextual meaning. Locate the exact clue before comparing the choices.",
        "passage": "Chart: eggs; newly hatched tailed swimmers; back legs appear; adult frog.",
        "prompt": "Which stage comes directly after the eggs?",
        "skill_ids": [
          "reading.event_sequence",
          "reading.word_meaning_context"
        ],
        "options": [
          "adult frog",
          "newly hatched tailed swimmers",
          "back legs appear",
          "dry nest"
        ],
        "accepted_answers": [
          "newly hatched tailed swimmers"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:guided:1",
          "teaching_block": "Use the stated stage features and transition clues to choose the next event or contextual meaning. Read the whole sentence, then test every option against its meaning.",
          "passage": "The ranger calls the newly hatched tailed swimmer a larva.",
          "prompt": "What does larva mean here?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "options": [
            "an early young stage",
            "a full-grown bird",
            "a dry seed",
            "an adult frog without a tail"
          ],
          "accepted_answers": [
            "an early young stage"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:guided:2",
          "teaching_block": "Use the stated stage features and transition clues to choose the next event or contextual meaning. Track who or what each detail belongs to before deciding.",
          "passage": "The small swimmer has a tail but no legs yet.",
          "prompt": "Which detail marks the early stage?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "options": [
            "it has four legs",
            "it has a tail and no legs",
            "it lives only on land",
            "it has feathers"
          ],
          "accepted_answers": [
            "it has a tail and no legs"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:guided:3",
          "teaching_block": "Locate the named event in the supplied sequence and inspect only its immediate neighbour.",
          "passage": "A tadpole first swims with a tail. Later, hind legs appear; front legs follow; finally the tail becomes much shorter.",
          "prompt": "Which event belongs immediately before the front legs appear?",
          "skill_ids": [
            "reading.event_sequence"
          ],
          "options": [
            "the adult lays eggs",
            "the hind legs appear",
            "the tail disappears before hatching",
            "the frog leaves the pond forever"
          ],
          "accepted_answers": [
            "the hind legs appear"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:guided:4",
          "teaching_block": "Test each possible meaning against the nearby clues muddy, beside, and water.",
          "passage": "The bank was soft and muddy, so the young frog left tiny marks beside the water.",
          "prompt": "What does bank mean in this sentence?",
          "skill_ids": [
            "reading.word_meaning_context"
          ],
          "options": [
            "a place that stores money",
            "a row of classroom desks",
            "the sloping land beside the water",
            "a machine that measures rain"
          ],
          "accepted_answers": [
            "the sloping land beside the water"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:independent:1",
          "teaching_block": "Reconstruct the supplied sequence and explain each stage word only from the evidence provided. Build the answer from two visible pieces of evidence.",
          "passage": "Supplied order: eggs in water; tailed swimmers hatch; legs appear; a young frog uses the bank.",
          "prompt": "Write the four stages in order using sequence words.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "eggs",
              "description": "Begins with eggs in water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "hatch",
              "description": "Places tailed swimmers after hatching.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "legs",
              "description": "Places leg growth next.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "bank",
              "description": "Ends with the young frog using the bank.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "eggs",
              "description": "Begins with eggs in water.",
              "any_of": [
                "first eggs",
                "eggs in water"
              ]
            },
            {
              "id": "hatch",
              "description": "Places tailed swimmers after hatching.",
              "any_of": [
                "then tailed swimmers",
                "eggs hatch"
              ]
            },
            {
              "id": "legs",
              "description": "Places leg growth next.",
              "any_of": [
                "legs appear",
                "next legs grow"
              ]
            },
            {
              "id": "bank",
              "description": "Ends with the young frog using the bank.",
              "any_of": [
                "finally uses the bank",
                "young frog reaches land"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "first",
            "eggs",
            "water",
            "then",
            "tailed"
          ],
          "model_answer": "First there are eggs in water. Then tailed swimmers hatch, legs appear, and finally the young frog begins using the bank. Reference evidence states: finally uses the bank.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "eggs",
            "hatch",
            "legs",
            "bank"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:independent:2",
          "teaching_block": "Reconstruct the supplied sequence and explain each stage word only from the evidence provided. State the relationship and support it with the relevant detail.",
          "passage": "A newly hatched animal has a tail, swims, and has not grown legs. The card labels it a larva.",
          "prompt": "Explain larva from the context and name two clues.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "meaning",
              "description": "Defines larva as an early young stage.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "clues",
              "description": "Uses tail/swimming and no legs as context clues.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meaning",
              "description": "Defines larva as an early young stage.",
              "any_of": [
                "early young stage",
                "newly hatched stage"
              ]
            },
            {
              "id": "clues",
              "description": "Uses tail/swimming and no legs as context clues.",
              "any_of": [
                "has a tail",
                "swims",
                "no legs"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "early",
            "young",
            "stage",
            "newly",
            "hatched"
          ],
          "model_answer": "Larva means an early young stage; its tail and lack of legs show that it has only recently hatched. Reference evidence states: has a tail.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:independent:3",
          "teaching_block": "Use the dates only to preserve order, and keep the retelling within the observation log's final boundary.",
          "passage": "Observation log: Day 1, round eggs in jelly; Day 8, swimming tadpoles; Day 28, tadpoles with hind legs; Day 43, froglets with four legs and short tails.",
          "prompt": "Retell the four stages in order without adding an adult stage that the log does not show.",
          "skill_ids": [
            "reading.event_sequence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "order",
              "description": "Preserves eggs, tadpoles, hind legs, then froglets.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Ends at the final recorded froglet stage.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "order",
              "description": "Preserves eggs, tadpoles, hind legs, then froglets.",
              "any_of": [
                "begins with round eggs in jelly"
              ]
            },
            {
              "id": "limit",
              "description": "Ends at the final recorded froglet stage.",
              "any_of": [
                "final recorded stage is a four-legged froglet"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "observation",
            "round",
            "eggs",
            "jelly",
            "swimming",
            "tadpoles",
            "with",
            "hind"
          ],
          "model_answer": "The log begins with round eggs in jelly, followed by swimming tadpoles. Hind legs then appear, and the final recorded stage is a four-legged froglet with a short tail.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "order",
            "limit"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:independent:4",
          "teaching_block": "Replace the target word with a candidate meaning, then use the sentence's spatial clues as evidence.",
          "passage": "The guide says, 'Stay on the path near the pond's edge because the ground beyond it is fragile.'",
          "prompt": "Explain edge from context and quote the clue that fixes its meaning.",
          "skill_ids": [
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "meaning",
              "description": "Defines edge as the pond's outer boundary.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "clue",
              "description": "Uses the path or ground beyond as context evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meaning",
              "description": "Defines edge as the pond's outer boundary.",
              "any_of": [
                "edge means the outer boundary"
              ]
            },
            {
              "id": "clue",
              "description": "Uses the path or ground beyond as context evidence.",
              "any_of": [
                "avoid the fragile ground beyond"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "guide",
            "says",
            "'stay",
            "path",
            "near",
            "pond's",
            "edge",
            "because"
          ],
          "model_answer": "Edge means the outer boundary beside the pond. The clue is that visitors must stay on the path near it and avoid the fragile ground beyond.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:transfer:1",
          "teaching_block": "Reconstruct the supplied sequence and explain each stage word only from the evidence provided. Explain the first part before connecting it to the result.",
          "passage": "Cards show back legs, then front legs, then a shortening tail.",
          "prompt": "Reconstruct the order and explain which transition happens last.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "order",
              "description": "Orders back legs, front legs, and tail shortening.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "last",
              "description": "Names tail shortening as the last supplied change.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "order",
              "description": "Orders back legs, front legs, and tail shortening.",
              "any_of": [
                "back legs then front legs",
                "tail shortens after"
              ]
            },
            {
              "id": "last",
              "description": "Names tail shortening as the last supplied change.",
              "any_of": [
                "tail shortening is last",
                "last the tail becomes shorter"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "back",
            "legs",
            "then",
            "front",
            "tail"
          ],
          "model_answer": "The back legs appear first, the front legs appear next, and the tail shortens last in the supplied sequence. Reference evidence states: back legs then front legs; tail shortening is last.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "order",
            "last"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:transfer:2",
          "teaching_block": "Reconstruct the supplied sequence and explain each stage word only from the evidence provided. Use your own words while preserving every required idea.",
          "passage": "A chart uses spawn for the egg group and tadpole for the tailed swimmer.",
          "prompt": "Explain both labels without saying the tadpole is an actual fish.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "spawn",
              "description": "Explains spawn as a group of frog eggs.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "tadpole",
              "description": "Explains tadpole as the young tailed frog stage.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "States that fish-like does not mean it is a fish.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "spawn",
              "description": "Explains spawn as a group of frog eggs.",
              "any_of": [
                "group of frog eggs",
                "frog eggs in water"
              ]
            },
            {
              "id": "tadpole",
              "description": "Explains tadpole as the young tailed frog stage.",
              "any_of": [
                "young frog stage",
                "tailed swimmer"
              ]
            },
            {
              "id": "boundary",
              "description": "States that fish-like does not mean it is a fish.",
              "any_of": [
                "not a fish",
                "fish-like comparison"
              ]
            }
          ],
          "forbidden_phrases": [
            "tadpole is a fish",
            "adult fish"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "group",
            "frog",
            "eggs",
            "water",
            "young"
          ],
          "model_answer": "Spawn is the group of frog eggs, while a tadpole is the young tailed frog stage; being fish-like does not make it a fish. Reference evidence states: young frog stage; not a fish.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:transfer:3",
          "teaching_block": "Transfer ordered retelling to a new life cycle and keep one explicit boundary around missing timing information.",
          "passage": "Butterfly card: egg on leaf; feeding caterpillar; pupa inside a case; winged adult emerges. The card gives no duration for any stage.",
          "prompt": "Transfer sequence reading to this life cycle and state its information limit.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "order",
              "description": "Preserves all four supplied stages.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "last",
              "description": "Ends with the winged adult.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "States that stage durations are absent.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "order",
              "description": "Preserves all four supplied stages.",
              "any_of": [
                "egg to a feeding caterpillar"
              ]
            },
            {
              "id": "last",
              "description": "Ends with the winged adult.",
              "any_of": [
                "finally to a winged adult"
              ]
            },
            {
              "id": "limit",
              "description": "States that stage durations are absent.",
              "any_of": [
                "does not say how long"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "butterfly",
            "card",
            "leaf",
            "feeding",
            "caterpillar",
            "pupa",
            "inside",
            "case"
          ],
          "model_answer": "The cycle moves from an egg to a feeding caterpillar, then to a pupa, and finally to a winged adult. The card does not say how long any stage lasts.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "order",
            "last",
            "limit"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:transfer:4",
          "teaching_block": "Order only the supplied stages and use the surrounding clues to explain each development word. Apply the same construct to this new passage. Use the visible passage to practise event sequence and word meaning context; include both details.",
          "passage": "Mosquito observation card: eggs rest on water; a wriggling larva moves below the surface; a pupa follows; an adult later emerges. Wriggling is shown by repeated twisting movement. No stage duration is listed.",
          "prompt": "Order the four stages, explain wriggling from context, and protect the missing timing fact.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_life_stage_and_words:transfer:4:order",
              "description": "Places all four supplied stages correctly.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_life_stage_and_words:transfer:4:meaning_limit",
              "description": "Defines wriggling and states the timing limit.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_life_stage_and_words:transfer:4:order",
              "description": "Places all four supplied stages correctly.",
              "any_of": [
                "eggs, larva, pupa, and adult"
              ]
            },
            {
              "id": "frog_life_stage_and_words:transfer:4:meaning_limit",
              "description": "Defines wriggling and states the timing limit.",
              "any_of": [
                "moving with repeated twists",
                "does not state how long"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "order",
            "larva",
            "adult"
          ],
          "model_answer": "The order is eggs, larva, pupa, and adult. Wriggling means moving with repeated twists below the water. The card does not state how long any stage lasts.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_life_stage_and_words:transfer:4:order",
            "frog_life_stage_and_words:transfer:4:meaning_limit"
          ]
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:review:1",
          "teaching_block": "Reconstruct the supplied sequence and explain each stage word only from the evidence provided. Apply the same reasoning to a different setting and justify it.",
          "passage": "A supplied observation records eggs on Monday, tailed swimmers later, and tiny back legs after more days.",
          "prompt": "Summarise only the observed order and avoid inventing exact timings.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "observations",
              "description": "Includes eggs, tailed swimmers, and back legs in order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "caution",
              "description": "Avoids exact durations not supplied.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "observations",
              "description": "Includes eggs, tailed swimmers, and back legs in order.",
              "any_of": [
                "eggs then tailed swimmers",
                "back legs appeared later"
              ]
            },
            {
              "id": "caution",
              "description": "Avoids exact durations not supplied.",
              "any_of": [
                "after more days",
                "later"
              ]
            }
          ],
          "forbidden_phrases": [
            "exactly two days",
            "exactly one week"
          ],
          "min_response_words": 17,
          "relevance_terms": [
            "eggs",
            "then",
            "tailed",
            "swimmers",
            "back"
          ],
          "model_answer": "The observation moved from eggs to tailed swimmers, and tiny back legs appeared later; the exact number of days was not supplied.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:review:2",
          "teaching_block": "Reconstruct the supplied sequence and explain each stage word only from the evidence provided. Separate what is stated from what can reasonably be inferred.",
          "passage": "A learner says every frog loses its tail at the exact same age. The supplied card only says the tail shortens during development.",
          "prompt": "Correct the claim using only the supplied evidence.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "correction",
              "description": "States only that the tail shortens during development.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Rejects the unsupported exact-age claim.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "correction",
              "description": "States only that the tail shortens during development.",
              "any_of": [
                "tail shortens during development",
                "becomes shorter as it develops"
              ]
            },
            {
              "id": "limit",
              "description": "Rejects the unsupported exact-age claim.",
              "any_of": [
                "exact age is not supplied",
                "cannot claim same age"
              ]
            }
          ],
          "forbidden_phrases": [
            "all frogs exactly",
            "same exact age"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "tail",
            "shortens",
            "during",
            "development",
            "becomes"
          ],
          "model_answer": "The card supports only that the tail shortens during development; it does not give an exact age or say every frog changes at the same time. Reference evidence states: exact age is not supplied.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:review:3",
          "teaching_block": "Order only the supplied stages and use the surrounding clues to explain each development word. Retrieve the construct, then verify it against the passage. Use the visible passage to practise event sequence and word meaning context; include both details.",
          "passage": "Bean diary: the seed coat splits; a root emerges downward; a shoot rises; the first leaves unfold. Emerges means comes out where it was not visible before.",
          "prompt": "Rewrite the development order and explain emerges using the change in visibility.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_life_stage_and_words:review:3:sequence",
              "description": "Orders splitting, root, shoot, and leaves.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_life_stage_and_words:review:3:word",
              "description": "Defines emerges from the visibility clue.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_life_stage_and_words:review:3:sequence",
              "description": "Orders splitting, root, shoot, and leaves.",
              "any_of": [
                "seed coat splits",
                "root emerges downward",
                "shoot rises",
                "leaves unfold"
              ]
            },
            {
              "id": "frog_life_stage_and_words:review:3:word",
              "description": "Defines emerges from the visibility clue.",
              "any_of": [
                "comes out and becomes visible"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "first",
            "splits",
            "emerges"
          ],
          "model_answer": "First the seed coat splits, then the root emerges downward, the shoot rises, and the first leaves unfold. Emerges means comes out and becomes visible.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_life_stage_and_words:review:3:sequence",
            "frog_life_stage_and_words:review:3:word"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_life_stage_and_words:review:4",
          "teaching_block": "Order only the supplied stages and use the surrounding clues to explain each development word. Retrieve the construct, then verify it against the passage. Use the visible passage to practise event sequence and word meaning context; include both details.",
          "passage": "Moth card: an egg hatches into a feeding caterpillar; the caterpillar forms a pupa; a winged moth emerges. The card calls the change gradual because it happens through several stages, but gives no dates.",
          "prompt": "State the sequence, explain gradual, and avoid adding exact ages.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_life_stage_and_words:review:4:stages",
              "description": "Orders the four stated life stages.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_life_stage_and_words:review:4:context",
              "description": "Defines gradual and protects the missing dates.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_life_stage_and_words:review:4:stages",
              "description": "Orders the four stated life stages.",
              "any_of": [
                "egg to caterpillar to pupa to winged moth"
              ]
            },
            {
              "id": "frog_life_stage_and_words:review:4:context",
              "description": "Defines gradual and protects the missing dates.",
              "any_of": [
                "through several stages",
                "gives no exact ages or dates"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "sequence",
            "moves",
            "caterpillar"
          ],
          "model_answer": "The sequence moves from egg to caterpillar to pupa to winged moth. Gradual means happening through several stages rather than all at once. The card gives no exact ages or dates.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_life_stage_and_words:review:4:stages",
            "frog_life_stage_and_words:review:4:context"
          ]
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "stage-order-or-fish-identity",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "misconception": "The learner treats fish-like as literally a fish, skips transition clues, or invents exact biological timings absent from the supplied source.",
          "remediation": "Build the sequence from labelled observation cards, define each stage from visible features, and mark any unsupplied timing claim as unknown.",
          "support_check_ids": [
            "frog_life_stage_and_words:support:bridge",
            "frog_life_stage_and_words:support:masterclass",
            "frog_life_stage_and_words:support:revision_level_1",
            "frog_life_stage_and_words:support:revision_level_2",
            "frog_life_stage_and_words:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:support:bridge",
          "teaching_block": "Use the stated stage features and transition clues to choose the next event or contextual meaning. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "Later, back legs appear before the front legs in the supplied chart.",
          "prompt": "Which event is earlier?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "options": [
            "front legs appear",
            "back legs appear",
            "the adult lays eggs again",
            "the tail is already gone"
          ],
          "accepted_answers": [
            "back legs appear"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:support:masterclass",
          "teaching_block": "Use the stated stage features and transition clues to choose the next event or contextual meaning. Reject any option that adds a fact the passage never gives.",
          "passage": "The note says the tail becomes shorter as the young frog develops.",
          "prompt": "What does develops mean here?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "options": [
            "changes and grows through stages",
            "stays exactly the same",
            "flies away",
            "builds a shell"
          ],
          "accepted_answers": [
            "changes and grows through stages"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:support:revision_level_1",
          "teaching_block": "Use the stated stage features and transition clues to choose the next event or contextual meaning. Break the task into one smaller decision and check it carefully.",
          "passage": "Sequence cards: legs grow; tail shortens; young frog uses the bank.",
          "prompt": "Which card comes last?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "options": [
            "legs grow",
            "tail shortens",
            "young frog uses the bank",
            "eggs are laid"
          ],
          "accepted_answers": [
            "young frog uses the bank"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:support:revision_level_2",
          "teaching_block": "Use the stated stage features and transition clues to choose the next event or contextual meaning. Name the rule first, then apply it to this new example.",
          "passage": "A tadpole is described as fish-like because it swims with a tail.",
          "prompt": "Which word shows this is a comparison, not identity?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "options": [
            "tadpole",
            "fish-like",
            "swims",
            "tail"
          ],
          "accepted_answers": [
            "fish-like"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "frog_life_stage_and_words:support:revision_level_3",
          "teaching_block": "Use the stated stage features and transition clues to choose the next event or contextual meaning. Compare the tempting error with the evidence that corrects it.",
          "passage": "The chart labels spawn as a group of frog eggs in water.",
          "prompt": "What does spawn mean in this chart?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.word_meaning_context"
          ],
          "options": [
            "frog eggs",
            "adult snakes",
            "dry leaves",
            "webbed feet"
          ],
          "accepted_answers": [
            "frog eggs"
          ]
        }
      }
    },
    {
      "level_id": "frog_adaptation_reasoning",
      "title": "Explain how frog features help",
      "focus": "infer function from body feature and situation",
      "outcome": "Write an evidence-based reason explaining how one supplied frog feature supports feeding, movement, hiding, or escape.",
      "skill_ids": [
        "reading.inference_reason",
        "writing.reason_answer"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch05:think:2"
      ],
      "connect": {
        "teaching_block": "An adaptation explanation links a feature or action to the problem it helps solve; it does not claim the feature guarantees survival.",
        "passage": "A speckled frog rests among speckled stones. The similar pattern makes its outline harder for a circling bird to notice.",
        "prompt": "Continue when you can explain how this example helps you infer function from body feature and situation."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "frog_adaptation_reasoning:co_construct",
        "teaching_block": "Identify the feature, the challenge, and the supported advantage before selecting a reason. Locate the exact clue before comparing the choices.",
        "passage": "A frog's colours resemble the leaves where it rests.",
        "prompt": "What advantage is supported?",
        "skill_ids": [
          "reading.inference_reason"
        ],
        "options": [
          "it becomes impossible to see",
          "it may be harder for a predator to notice",
          "it can change every leaf",
          "it no longer needs shelter"
        ],
        "accepted_answers": [
          "it may be harder for a predator to notice"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "frog_adaptation_reasoning:guided:1",
          "teaching_block": "Identify the feature, the challenge, and the supported advantage before selecting a reason. Read the whole sentence, then test every option against its meaning.",
          "passage": "A frog flicks a fast sticky tongue towards a nearby moth.",
          "prompt": "How does the feature help?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "it reaches food quickly",
            "it builds a nest",
            "it cools the pond",
            "it warns every snake"
          ],
          "accepted_answers": [
            "it reaches food quickly"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:guided:2",
          "teaching_block": "Explain the feature-to-function link with evidence and avoid absolute claims such as always or invisible. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "A brown frog stays still on brown bark while a bird passes overhead.",
          "prompt": "Write a complete because sentence explaining the supported advantage.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "match",
              "description": "Names the colour match between frog and bark.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains that the match may reduce notice.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "match",
              "description": "Names the colour match between frog and bark.",
              "any_of": [
                "brown frog matches brown bark",
                "blends with bark"
              ]
            },
            {
              "id": "reason",
              "description": "Explains that the match may reduce notice.",
              "any_of": [
                "harder to notice",
                "bird may not see"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "brown",
            "frog",
            "matches",
            "bark",
            "blends"
          ],
          "model_answer": "The frog may be harder to notice because its brown colour blends with the bark. Reference evidence states: brown frog matches brown bark.",
          "pass_score": 0.8
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_adaptation_reasoning:guided:3",
          "teaching_block": "Connect the named body feature to the exact challenge in the habitat; reject unrelated benefits.",
          "passage": "A tree frog has sticky toe pads and rests on smooth leaves above the ground.",
          "prompt": "Which explanation best matches feature to advantage?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "Sticky toe pads help the frog grip smooth leaves without slipping.",
            "Sticky toe pads make every leaf grow larger.",
            "The pads allow the frog to breathe underwater forever.",
            "The pads prove that the frog never climbs."
          ],
          "accepted_answers": [
            "Sticky toe pads help the frog grip smooth leaves without slipping."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_adaptation_reasoning:guided:4",
          "teaching_block": "Use position and behaviour together: ask what the raised parts can do while the body stays submerged.",
          "passage": "A pond frog's eyes and nostrils sit high on its head while most of its body remains below the surface.",
          "prompt": "What advantage is most directly supported?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "It can read signs underneath the pond.",
            "It can see and breathe while keeping much of its body hidden in water.",
            "It no longer needs air at any life stage.",
            "It can dry the pond by opening its eyes."
          ],
          "accepted_answers": [
            "It can see and breathe while keeping much of its body hidden in water."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:independent:1",
          "teaching_block": "Explain the feature-to-function link with evidence and avoid absolute claims such as always or invisible. Build the answer from two visible pieces of evidence.",
          "passage": "A mottled frog rests among dead leaves while a snake passes nearby without turning towards it.",
          "prompt": "Explain how the frog's appearance may reduce danger.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "match",
              "description": "States that the mottled colour matches the dead leaves.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "advantage",
              "description": "Explains that matching makes the frog harder to notice.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "match",
              "description": "States that the mottled colour matches the dead leaves.",
              "any_of": [
                "matches the dead leaves",
                "blends with leaves"
              ]
            },
            {
              "id": "advantage",
              "description": "Explains that matching makes the frog harder to notice.",
              "any_of": [
                "harder to notice",
                "snake may miss it"
              ]
            }
          ],
          "forbidden_phrases": [
            "completely invisible",
            "guarantees safety"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "matches",
            "dead",
            "leaves",
            "blends",
            "with"
          ],
          "model_answer": "The mottled colour blends with the dead leaves, so the frog may be harder for the snake to notice. Reference evidence states: matches the dead leaves; harder to notice.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:independent:2",
          "teaching_block": "Explain the feature-to-function link with evidence and avoid absolute claims such as always or invisible. State the relationship and support it with the relevant detail.",
          "passage": "A frog waits near an insect, then extends its tongue quickly instead of chasing it.",
          "prompt": "Why is the tongue useful in this scene?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "reach",
              "description": "Explains that the tongue reaches the nearby insect quickly.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "contrast",
              "description": "Notes that the frog need not chase the insect first.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "reach",
              "description": "Explains that the tongue reaches the nearby insect quickly.",
              "any_of": [
                "reaches the insect quickly",
                "fast tongue catches"
              ]
            },
            {
              "id": "contrast",
              "description": "Notes that the frog need not chase the insect first.",
              "any_of": [
                "without chasing",
                "does not need a long chase"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "reaches",
            "insect",
            "quickly",
            "fast",
            "tongue"
          ],
          "model_answer": "The fast tongue reaches the nearby insect quickly, allowing the frog to catch it without a long chase. Reference evidence states: reaches the insect quickly; without chasing.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:independent:3",
          "teaching_block": "Name the environmental problem first, then explain the mechanism before stating the resulting advantage.",
          "passage": "During a dry afternoon, a small frog presses itself beneath damp leaf litter. Its skin loses moisture quickly in open sun.",
          "prompt": "Explain how the behaviour matches the problem and what advantage it gives.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "match",
              "description": "Links damp cover to avoiding direct sun and moisture loss.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "advantage",
              "description": "States the hydration advantage.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "match",
              "description": "Links damp cover to avoiding direct sun and moisture loss.",
              "any_of": [
                "damp leaf litter keeps the frog away from direct sun"
              ]
            },
            {
              "id": "advantage",
              "description": "States the hydration advantage.",
              "any_of": [
                "helps it remain hydrated"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "during",
            "afternoon",
            "small",
            "frog",
            "presses",
            "itself",
            "beneath",
            "damp"
          ],
          "model_answer": "Hiding beneath damp leaf litter keeps the frog away from direct sun and slows moisture loss from its skin. This helps it remain hydrated during the dry afternoon.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:independent:4",
          "teaching_block": "Build a bounded inference from the observed pattern and the stated obstacle without inventing an animal intention.",
          "passage": "A frog beside a noisy stream gives a short repeated call from an exposed rock. The repeated pattern can be heard between bursts of water noise.",
          "prompt": "Infer why repetition may be useful, using the supplied sound condition as evidence.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "inference",
              "description": "Explains that repetition creates several chances to hear the call.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Uses the bursts of stream noise as evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "inference",
              "description": "Explains that repetition creates several chances to hear the call.",
              "any_of": [
                "gives listeners several chances to hear"
              ]
            },
            {
              "id": "evidence",
              "description": "Uses the bursts of stream noise as evidence.",
              "any_of": [
                "between bursts of stream noise"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "frog",
            "beside",
            "noisy",
            "stream",
            "gives",
            "short",
            "repeated",
            "call"
          ],
          "model_answer": "Repeating the short call gives listeners several chances to hear it between bursts of stream noise. The noisy water makes one brief call easier to miss.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:transfer:1",
          "teaching_block": "Explain the feature-to-function link with evidence and avoid absolute claims such as always or invisible. Explain the first part before connecting it to the result.",
          "passage": "A frog jumps with long hind legs on land and pushes water with webbed back feet in the pond.",
          "prompt": "Explain how the two features support different movements.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "hind_legs",
              "description": "Links long hind legs with jumping on land.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "webbing",
              "description": "Links webbed feet with pushing water while swimming.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "hind_legs",
              "description": "Links long hind legs with jumping on land.",
              "any_of": [
                "hind legs support jumping",
                "long legs push off land"
              ]
            },
            {
              "id": "webbing",
              "description": "Links webbed feet with pushing water while swimming.",
              "any_of": [
                "webbed feet push water",
                "webbing supports swimming"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 16,
          "relevance_terms": [
            "hind",
            "legs",
            "support",
            "jumping",
            "long"
          ],
          "model_answer": "Long hind legs help the frog push off for a jump on land, while webbed back feet push water during swimming. Reference evidence states: hind legs support jumping; webbed feet push water.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:transfer:2",
          "teaching_block": "Explain the feature-to-function link with evidence and avoid absolute claims such as always or invisible. Use your own words while preserving every required idea.",
          "passage": "A shadow crosses a pool. The frog first stays still against a stone and then dives under a ledge.",
          "prompt": "Explain how each action addresses danger differently.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "still",
              "description": "Explains that staying still reduces noticeable movement.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "dive",
              "description": "Explains that diving provides physical cover or distance.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "still",
              "description": "Explains that staying still reduces noticeable movement.",
              "any_of": [
                "reduces movement",
                "harder to notice"
              ]
            },
            {
              "id": "dive",
              "description": "Explains that diving provides physical cover or distance.",
              "any_of": [
                "gets under cover",
                "moves away from danger"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "reduces",
            "movement",
            "harder",
            "notice",
            "gets"
          ],
          "model_answer": "Staying still reduces movement that could attract attention, while diving under the ledge gives the frog physical cover. Reference evidence states: gets under cover.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:transfer:3",
          "teaching_block": "Transfer the feature-mechanism-advantage chain to a new animal and preserve the source card's missing-information boundary.",
          "passage": "A water bird has long spread-out toes and walks across soft mud without sinking deeply. The card gives no information about its flight speed.",
          "prompt": "Transfer feature-advantage reasoning and include the information limit.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "feature",
              "description": "Uses long spread-out toes as the feature.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "advantage",
              "description": "Explains reduced sinking in soft mud.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Rejects a flight-speed conclusion.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "feature",
              "description": "Uses long spread-out toes as the feature.",
              "any_of": [
                "long spread-out toes distribute its weight"
              ]
            },
            {
              "id": "advantage",
              "description": "Explains reduced sinking in soft mud.",
              "any_of": [
                "does not sink deeply"
              ]
            },
            {
              "id": "limit",
              "description": "Rejects a flight-speed conclusion.",
              "any_of": [
                "no evidence about flight speed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "water",
            "bird",
            "long",
            "spread",
            "toes",
            "walks",
            "across",
            "soft"
          ],
          "model_answer": "The bird's long spread-out toes distribute its weight across more mud, so it does not sink deeply while walking. The card provides no evidence about flight speed.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:transfer:4",
          "teaching_block": "Link a supplied body feature or action to a specific advantage without making a universal claim. Apply the same construct to this new passage. Use the visible passage to practise inference reason and reason answer; include both details.",
          "passage": "A desert lizard has pale scales that match dry sand and wide toes that spread its weight on loose ground. The card gives no information about cold weather.",
          "prompt": "Explain how each feature may help in this setting and include the evidence limit.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_adaptation_reasoning:transfer:4:features",
              "description": "Links colour and toe shape to their setting advantages.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_adaptation_reasoning:transfer:4:limit",
              "description": "States that cold-weather survival is unsupported.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_adaptation_reasoning:transfer:4:features",
              "description": "Links colour and toe shape to their setting advantages.",
              "any_of": [
                "harder to notice against dry sand",
                "wide toes spread weight"
              ]
            },
            {
              "id": "frog_adaptation_reasoning:transfer:4:limit",
              "description": "States that cold-weather survival is unsupported.",
              "any_of": [
                "no evidence about cold-weather survival"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "scales",
            "lizard",
            "harder"
          ],
          "model_answer": "The pale scales may make the lizard harder to notice against dry sand, while its wide toes spread weight and help it move on loose ground. The card gives no evidence about cold-weather survival.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:review:1",
          "teaching_block": "Explain the feature-to-function link with evidence and avoid absolute claims such as always or invisible. Apply the same reasoning to a different setting and justify it.",
          "passage": "A duck and a frog both have webbing between toes, but the frog also uses long hind legs to jump onto land.",
          "prompt": "Explain one shared function and one frog-specific movement.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "shared",
              "description": "States that webbing helps both push water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog",
              "description": "States that the frog's hind legs support jumping.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "shared",
              "description": "States that webbing helps both push water.",
              "any_of": [
                "both push water",
                "webbing supports swimming"
              ]
            },
            {
              "id": "frog",
              "description": "States that the frog's hind legs support jumping.",
              "any_of": [
                "hind legs help it jump",
                "jumps onto land"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "both",
            "push",
            "water",
            "webbing",
            "supports"
          ],
          "model_answer": "Both animals use webbed feet to push water, while the frog's long hind legs also help it jump onto land. Reference evidence states: both push water; hind legs help it jump.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:review:2",
          "teaching_block": "Explain the feature-to-function link with evidence and avoid absolute claims such as always or invisible. Separate what is stated from what can reasonably be inferred.",
          "passage": "A learner says camouflage makes every frog invisible everywhere.",
          "prompt": "Correct the claim using a precise feature-to-setting reason.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "limit",
              "description": "Rejects the absolute invisible-everywhere claim.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "match",
              "description": "Explains that camouflage helps when appearance matches a particular setting.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "limit",
              "description": "Rejects the absolute invisible-everywhere claim.",
              "any_of": [
                "does not make a frog invisible everywhere",
                "does not guarantee hiding"
              ]
            },
            {
              "id": "match",
              "description": "Explains that camouflage helps when appearance matches a particular setting.",
              "any_of": [
                "matches the setting",
                "harder to notice among similar colours"
              ]
            }
          ],
          "forbidden_phrases": [
            "camouflage makes every frog invisible everywhere",
            "never seen"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "invisible",
            "everywhere",
            "does",
            "guarantee",
            "hiding"
          ],
          "model_answer": "Camouflage does not make a frog invisible everywhere; it may make the frog harder to notice when its appearance matches the setting.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:review:3",
          "teaching_block": "Link a supplied body feature or action to a specific advantage without making a universal claim. Retrieve the construct, then verify it against the passage. Use the visible passage to practise inference reason and reason answer; include both details.",
          "passage": "A kingfisher waits above a stream and has a long pointed beak. The card says it dives toward small fish near the surface.",
          "prompt": "Write a reasoned feature-to-action explanation without claiming the beak guarantees success.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_adaptation_reasoning:review:3:reason",
              "description": "Links the beak shape to reaching or grasping fish.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_adaptation_reasoning:review:3:boundary",
              "description": "Avoids a universal success claim.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_adaptation_reasoning:review:3:reason",
              "description": "Links the beak shape to reaching or grasping fish.",
              "any_of": [
                "beak may help",
                "grasp small fish"
              ]
            },
            {
              "id": "frog_adaptation_reasoning:review:3:boundary",
              "description": "Avoids a universal success claim.",
              "any_of": [
                "does not guarantee",
                "every attempt succeeds"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "pointed",
            "kingfisher",
            "reach"
          ],
          "model_answer": "The long pointed beak may help the kingfisher reach and grasp small fish during a dive, but the feature does not guarantee that every attempt succeeds.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "frog_adaptation_reasoning:review:4",
          "teaching_block": "Link a supplied body feature or action to a specific advantage without making a universal claim. Retrieve the construct, then verify it against the passage. Use the visible passage to practise inference reason and reason answer; include both details.",
          "passage": "A snail withdraws into its hard shell when a shadow passes, then emerges after the ground is quiet again.",
          "prompt": "Explain how the response may reduce danger and why it is not proof of complete safety.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_adaptation_reasoning:review:4:advantage",
              "description": "Links withdrawal and shell to shielding the soft body.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_adaptation_reasoning:review:4:precision",
              "description": "States that reduced exposure is not total safety.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_adaptation_reasoning:review:4:advantage",
              "description": "Links withdrawal and shell to shielding the soft body.",
              "any_of": [
                "shield the snail's soft body",
                "danger is near"
              ]
            },
            {
              "id": "frog_adaptation_reasoning:review:4:precision",
              "description": "States that reduced exposure is not total safety.",
              "any_of": [
                "reduces exposure",
                "does not prove",
                "completely safe"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "withdrawing",
            "shell",
            "shield"
          ],
          "model_answer": "Withdrawing into the hard shell may shield the snail's soft body while danger is near. It reduces exposure, but it does not prove the snail is completely safe from every threat.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "feature-without-function-or-absolute",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "misconception": "The learner names a body feature without explaining its function, or turns a limited advantage into an absolute guarantee.",
          "remediation": "Use a feature-challenge-advantage frame and replace absolute words with evidence-sized language such as may or helps.",
          "support_check_ids": [
            "frog_adaptation_reasoning:support:bridge",
            "frog_adaptation_reasoning:support:masterclass",
            "frog_adaptation_reasoning:support:revision_level_1",
            "frog_adaptation_reasoning:support:revision_level_2",
            "frog_adaptation_reasoning:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "frog_adaptation_reasoning:support:bridge",
          "teaching_block": "Identify the feature, the challenge, and the supported advantage before selecting a reason. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "Long hind legs straighten as the frog leaves the bank.",
          "prompt": "What action do they support?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "jumping",
            "chewing",
            "singing",
            "building"
          ],
          "accepted_answers": [
            "jumping"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "frog_adaptation_reasoning:support:masterclass",
          "teaching_block": "Identify the feature, the challenge, and the supported advantage before selecting a reason. Reject any option that adds a fact the passage never gives.",
          "passage": "A frog freezes against brown bark, then slips under a root when a shadow returns.",
          "prompt": "How do the two actions differ?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "both make the frog louder",
            "freezing reduces notice; the root gives cover",
            "the root changes its colour",
            "freezing catches food"
          ],
          "accepted_answers": [
            "freezing reduces notice; the root gives cover"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "frog_adaptation_reasoning:support:revision_level_1",
          "teaching_block": "Identify the feature, the challenge, and the supported advantage before selecting a reason. Break the task into one smaller decision and check it carefully.",
          "passage": "The frog dives when footsteps approach the pond.",
          "prompt": "Which reason best fits?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "water can provide an escape route",
            "the frog wants to become a fish",
            "footsteps make water warmer",
            "diving guarantees no danger"
          ],
          "accepted_answers": [
            "water can provide an escape route"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "frog_adaptation_reasoning:support:revision_level_2",
          "teaching_block": "Identify the feature, the challenge, and the supported advantage before selecting a reason. Name the rule first, then apply it to this new example.",
          "passage": "A male frog's throat pouch vibrates and makes its call carry farther.",
          "prompt": "Which relationship is stated?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "vibration amplifies the call",
            "the pouch stores water",
            "the call creates webbed feet",
            "the pond vibrates the frog"
          ],
          "accepted_answers": [
            "vibration amplifies the call"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "frog_adaptation_reasoning:support:revision_level_3",
          "teaching_block": "Identify the feature, the challenge, and the supported advantage before selecting a reason. Compare the tempting error with the evidence that corrects it.",
          "passage": "A toad's rougher skin and shorter hops are compared with a frog's smoother skin and longer jumps.",
          "prompt": "Which answer uses the supplied comparison?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "toads and frogs are identical",
            "the frog is smoother and often jumps farther",
            "all toads live only in deserts",
            "frogs never walk"
          ],
          "accepted_answers": [
            "the frog is smoother and often jumps farther"
          ]
        }
      }
    },
    {
      "level_id": "frog_comparison",
      "title": "Compare frogs with other animals",
      "focus": "state one accurate similarity and one precise difference",
      "outcome": "Write a connected comparison naming both animals, one supported similarity, and one supported difference from the supplied fact card.",
      "skill_ids": [
        "reading.sentence_comprehension",
        "writing.compare_contrast"
      ],
      "episode_kind": "expression_workshop",
      "source_anchor_ids": [
        "eng_c5_ch05:think:2",
        "eng_c5_ch05:write:7"
      ],
      "connect": {
        "teaching_block": "A useful comparison names both subjects and uses the same feature category for the similarity or difference instead of listing unrelated facts.",
        "passage": "Fact card: a frog and fish can both move through water. A frog kicks with legs and can use land, while a fish moves with fins and remains in water.",
        "prompt": "Continue when you can explain how this example helps you state one accurate similarity and one precise difference."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "frog_comparison:co_construct",
        "teaching_block": "Compare the same category across both animals and reject one-sided or unsupported statements. Locate the exact clue before comparing the choices.",
        "passage": "Frog: kicks with legs and can use land. Fish: swims with fins and stays in water.",
        "prompt": "Which statement is a valid difference?",
        "skill_ids": [
          "reading.sentence_comprehension"
        ],
        "options": [
          "both are animals",
          "the frog uses legs while the fish uses fins",
          "both live only on land",
          "the fish has webbed feet"
        ],
        "accepted_answers": [
          "the frog uses legs while the fish uses fins"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "frog_comparison:guided:1",
          "teaching_block": "Compare the same category across both animals and reject one-sided or unsupported statements. Read the whole sentence, then test every option against its meaning.",
          "passage": "Frog and duck both push water with webbed feet.",
          "prompt": "Which relationship is stated?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "a similarity in swimming support",
            "a difference in skin",
            "a difference in diet",
            "proof they are the same animal"
          ],
          "accepted_answers": [
            "a similarity in swimming support"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:guided:2",
          "teaching_block": "Name both animals, connect one accurate similarity with one precise difference, and stay within the supplied facts. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "Frog and duck: both have webbed feet. Duck: feathers. Frog: smooth skin.",
          "prompt": "Write one sentence with both the similarity and difference.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "same",
              "description": "States that both have webbed feet.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "different",
              "description": "Contrasts feathers with smooth skin.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "same",
              "description": "States that both have webbed feet.",
              "any_of": [
                "both have webbed feet"
              ]
            },
            {
              "id": "different",
              "description": "Contrasts feathers with smooth skin.",
              "any_of": [
                "duck has feathers",
                "frog has smooth skin"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 16,
          "relevance_terms": [
            "both",
            "have",
            "webbed",
            "feet",
            "duck"
          ],
          "model_answer": "Both the frog and duck have webbed feet, but the duck has feathers while the frog has smooth skin. Reference evidence states: both have webbed feet.",
          "pass_score": 0.8
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_comparison:guided:3",
          "teaching_block": "Compare the same feature on both cards and keep every claim inside the supplied facts.",
          "passage": "Frog card: moist skin, four legs, eggs laid in water. Fish card: scales, fins, eggs laid in water.",
          "prompt": "Which comparison uses one supported similarity and one supported difference?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "Both have scales and live only on land.",
            "Both lay eggs in water, but the frog has legs while the fish has fins.",
            "The fish has four legs, unlike the frog.",
            "Only the frog lays eggs in water."
          ],
          "accepted_answers": [
            "Both lay eggs in water, but the frog has legs while the fish has fins."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_comparison:guided:4",
          "teaching_block": "Hold the shared feature constant, then state the one visible stage difference with a contrast connector.",
          "passage": "Froglet: four legs and a shrinking tail. Adult frog: four legs and no visible tail.",
          "prompt": "Which sentence expresses the contrast precisely?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "Only the adult frog has four legs.",
            "Both have long permanent tails.",
            "Both have four legs, whereas only the froglet still has a shrinking tail.",
            "The froglet has fins instead of legs."
          ],
          "accepted_answers": [
            "Both have four legs, whereas only the froglet still has a shrinking tail."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:independent:1",
          "teaching_block": "Name both animals, connect one accurate similarity with one precise difference, and stay within the supplied facts. Build the answer from two visible pieces of evidence.",
          "passage": "Frog: swims by kicking webbed back feet and can hop on land. Fish: swims with fins and remains in water.",
          "prompt": "Compare the frog and fish with one similarity and one difference.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "similarity",
              "description": "States that both can move through water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "difference",
              "description": "Contrasts legs/land use with fins/water-only use.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "similarity",
              "description": "States that both can move through water.",
              "any_of": [
                "both swim",
                "both move through water"
              ]
            },
            {
              "id": "difference",
              "description": "Contrasts legs/land use with fins/water-only use.",
              "any_of": [
                "frog uses legs",
                "fish uses fins",
                "frog can use land"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "both",
            "swim",
            "move",
            "through",
            "water"
          ],
          "model_answer": "Both the frog and fish can move through water, but the frog kicks with legs and can hop on land while the fish swims with fins and remains in water. Reference evidence states: both swim; frog uses legs.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:independent:2",
          "teaching_block": "Name both animals, connect one accurate similarity with one precise difference, and stay within the supplied facts. State the relationship and support it with the relevant detail.",
          "passage": "Frog: smooth moist-looking skin and long jumps. Toad: bumpier drier-looking skin and shorter hops.",
          "prompt": "Write a connected comparison using both skin and movement.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "skin",
              "description": "Contrasts smooth/moist-looking and bumpy/drier-looking skin.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "movement",
              "description": "Contrasts longer jumps with shorter hops.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "skin",
              "description": "Contrasts smooth/moist-looking and bumpy/drier-looking skin.",
              "any_of": [
                "smooth skin",
                "bumpy skin",
                "drier skin"
              ]
            },
            {
              "id": "movement",
              "description": "Contrasts longer jumps with shorter hops.",
              "any_of": [
                "long jumps",
                "shorter hops"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "smooth",
            "skin",
            "bumpy",
            "drier",
            "long"
          ],
          "model_answer": "A frog usually has smoother, moist-looking skin and makes longer jumps, while a toad has bumpier, drier-looking skin and takes shorter hops. Reference evidence states: smooth skin.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:independent:3",
          "teaching_block": "Select comparable features from both cards, then organize similarity before matched differences.",
          "passage": "Pond frog: webbed hind feet, moist skin, strong jumps. Tree frog: sticky toe pads, moist skin, climbs smooth leaves.",
          "prompt": "Write two sentences with one supported similarity and two matched differences.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "similarity",
              "description": "States the shared moist skin.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "difference",
              "description": "Contrasts webbed feet with sticky toe pads.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "behaviour",
              "description": "Contrasts jumping with leaf climbing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "similarity",
              "description": "States the shared moist skin.",
              "any_of": [
                "both frogs have moist skin"
              ]
            },
            {
              "id": "difference",
              "description": "Contrasts webbed feet with sticky toe pads.",
              "any_of": [
                "webbed hind feet for swimming"
              ]
            },
            {
              "id": "behaviour",
              "description": "Contrasts jumping with leaf climbing.",
              "any_of": [
                "tree frog has sticky toe pads and climbs"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "pond",
            "frog",
            "webbed",
            "hind",
            "feet",
            "moist",
            "skin",
            "strong"
          ],
          "model_answer": "Both frogs have moist skin. The pond frog has webbed hind feet for swimming and makes strong jumps, whereas the tree frog has sticky toe pads and climbs smooth leaves.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:independent:4",
          "teaching_block": "Compare like with like: movement against movement and body form against body form, using only card evidence.",
          "passage": "Tadpole: lives in water, swims with a tail, has no legs at first. Froglet: has four legs, a short remaining tail, and can reach the bank.",
          "prompt": "Compare movement and body form without claiming facts outside the cards.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "tadpole",
              "description": "Describes tail swimming and absent early legs.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "froglet",
              "description": "Describes four legs and a short tail.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "tadpole",
              "description": "Describes tail swimming and absent early legs.",
              "any_of": [
                "tadpole swims with a long tail"
              ]
            },
            {
              "id": "froglet",
              "description": "Describes four legs and a short tail.",
              "any_of": [
                "froglet moves with four legs"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "tadpole",
            "lives",
            "water",
            "swims",
            "with",
            "tail",
            "legs",
            "first"
          ],
          "model_answer": "The tadpole swims with a long tail and begins without legs, while the froglet moves with four legs and keeps only a short tail. The froglet can also reach the bank.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:transfer:1",
          "teaching_block": "Name both animals, connect one accurate similarity with one precise difference, and stay within the supplied facts. Explain the first part before connecting it to the result.",
          "passage": "Frog: webbed feet and smooth skin. Duck: webbed feet, feathers, wings, and a bill.",
          "prompt": "State one similarity and one difference using the same fact card.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "similarity",
              "description": "States that both have webbed feet.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "difference",
              "description": "Contrasts feathers/wings/bill with frog skin or body.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "similarity",
              "description": "States that both have webbed feet.",
              "any_of": [
                "both have webbed feet"
              ]
            },
            {
              "id": "difference",
              "description": "Contrasts feathers/wings/bill with frog skin or body.",
              "any_of": [
                "duck has feathers",
                "frog has smooth skin",
                "duck has a bill"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 17,
          "relevance_terms": [
            "both",
            "have",
            "webbed",
            "feet",
            "duck"
          ],
          "model_answer": "Both animals have webbed feet, but the duck has feathers and a bill while the frog has smooth skin. Reference evidence states: both have webbed feet.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:transfer:2",
          "teaching_block": "Name both animals, connect one accurate similarity with one precise difference, and stay within the supplied facts. Use your own words while preserving every required idea.",
          "passage": "Frog: long hind legs for jumping. Lizard: four legs used for walking and running in the supplied card.",
          "prompt": "Compare how the two animals use their legs.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog",
              "description": "Links frog hind legs to jumping.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "lizard",
              "description": "Links lizard legs to walking or running.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog",
              "description": "Links frog hind legs to jumping.",
              "any_of": [
                "frog jumps with hind legs",
                "long hind legs"
              ]
            },
            {
              "id": "lizard",
              "description": "Links lizard legs to walking or running.",
              "any_of": [
                "lizard walks",
                "lizard runs"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "frog",
            "jumps",
            "with",
            "hind",
            "legs"
          ],
          "model_answer": "The frog uses long hind legs for jumping, whereas the lizard uses its four legs mainly for walking and running in the supplied card. Reference evidence states: lizard walks.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:transfer:3",
          "teaching_block": "Transfer the same-feature comparison structure to a new life cycle and avoid adding unsupplied size or speed claims.",
          "passage": "Dragonfly nymph: aquatic, six legs, no working adult wings. Adult dragonfly: flies above water, six legs, two pairs of working wings.",
          "prompt": "Transfer the comparison frame to these two stages using one similarity and two differences.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "similarity",
              "description": "States that both stages have six legs.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "habitat",
              "description": "Contrasts aquatic and above-water movement.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wings",
              "description": "Contrasts absent working wings with two working pairs.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "similarity",
              "description": "States that both stages have six legs.",
              "any_of": [
                "both stages have six legs"
              ]
            },
            {
              "id": "habitat",
              "description": "Contrasts aquatic and above-water movement.",
              "any_of": [
                "nymph lives in water"
              ]
            },
            {
              "id": "wings",
              "description": "Contrasts absent working wings with two working pairs.",
              "any_of": [
                "two pairs of working wings"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "dragonfly",
            "nymph",
            "aquatic",
            "legs",
            "working",
            "adult",
            "wings",
            "flies"
          ],
          "model_answer": "Both stages have six legs. The nymph lives in water and lacks working adult wings, whereas the adult flies above water with two pairs of working wings.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:transfer:4",
          "teaching_block": "Compare the same feature for both subjects and replace opinions with details from the fact card. Apply the same construct to this new passage. Use the visible passage to practise sentence comprehension and compare contrast; include both details.",
          "passage": "Otter card: swims with webbed feet and catches food in water. Beaver card: swims with webbed hind feet and cuts branches with strong front teeth. Both rest on land.",
          "prompt": "Write one supported similarity and two matched differences.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_comparison:transfer:4:similarity",
              "description": "States the shared swimming feature or land rest.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_comparison:transfer:4:difference",
              "description": "Contrasts food catching with branch cutting.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_comparison:transfer:4:similarity",
              "description": "States the shared swimming feature or land rest.",
              "any_of": [
                "Both animals swim with webbed feet",
                "rest on land"
              ]
            },
            {
              "id": "frog_comparison:transfer:4:difference",
              "description": "Contrasts food catching with branch cutting.",
              "any_of": [
                "otter catches food",
                "beaver uses strong front teeth"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "animals",
            "webbed",
            "otter"
          ],
          "model_answer": "Both animals swim with webbed feet and can rest on land. The otter catches food in water, while the beaver uses strong front teeth to cut branches.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:review:1",
          "teaching_block": "Name both animals, connect one accurate similarity with one precise difference, and stay within the supplied facts. Apply the same reasoning to a different setting and justify it.",
          "passage": "Frog and turtle can both enter water. The frog has long jumping legs; the turtle has a hard shell.",
          "prompt": "Write one similarity and one body-feature difference.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "similarity",
              "description": "States that both can enter water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "difference",
              "description": "Contrasts long legs with a hard shell.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "similarity",
              "description": "States that both can enter water.",
              "any_of": [
                "both enter water",
                "both use water"
              ]
            },
            {
              "id": "difference",
              "description": "Contrasts long legs with a hard shell.",
              "any_of": [
                "frog has long legs",
                "turtle has a hard shell"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "both",
            "enter",
            "water",
            "frog",
            "long"
          ],
          "model_answer": "Both the frog and turtle can enter water, but the frog has long legs for jumping while the turtle has a hard shell. Reference evidence states: both enter water.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:review:2",
          "teaching_block": "Name both animals, connect one accurate similarity with one precise difference, and stay within the supplied facts. Separate what is stated from what can reasonably be inferred.",
          "passage": "A learner writes, 'Frogs and fish are different because frogs are nice.' The fact card gives legs, fins, land use, and water use.",
          "prompt": "Replace the vague opinion with an evidence-based comparison.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_fact",
              "description": "Uses a frog fact from legs or land use.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "fish_fact",
              "description": "Uses a fish fact from fins or remaining in water.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_fact",
              "description": "Uses a frog fact from legs or land use.",
              "any_of": [
                "frog uses legs",
                "frog can use land"
              ]
            },
            {
              "id": "fish_fact",
              "description": "Uses a fish fact from fins or remaining in water.",
              "any_of": [
                "fish uses fins",
                "fish remains in water"
              ]
            }
          ],
          "forbidden_phrases": [
            "because frogs are nice",
            "I like frogs more"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "frog",
            "uses",
            "legs",
            "land",
            "fish"
          ],
          "model_answer": "A frog uses legs and can move onto land, while a fish swims with fins and remains in water. Reference evidence states: fish uses fins.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:review:3",
          "teaching_block": "Compare the same feature for both subjects and replace opinions with details from the fact card. Retrieve the construct, then verify it against the passage. Use the visible passage to practise sentence comprehension and compare contrast; include both details.",
          "passage": "Butterfly card: clubbed antennae, often rests with wings upright. Moth card: feathery antennae, often rests with wings spread. Both have scaled wings.",
          "prompt": "Compare the same three features without claiming that the pattern has no exceptions.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_comparison:review:3:shared",
              "description": "States the scaled-wing similarity.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_comparison:review:3:contrast",
              "description": "Matches antenna and resting-wing differences.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_comparison:review:3:shared",
              "description": "States the scaled-wing similarity.",
              "any_of": [
                "Both insects have scaled wings"
              ]
            },
            {
              "id": "frog_comparison:review:3:contrast",
              "description": "Matches antenna and resting-wing differences.",
              "any_of": [
                "clubbed antennae",
                "upright resting wings",
                "feathery antennae",
                "spread resting wings"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "insects",
            "scaled",
            "wings"
          ],
          "model_answer": "Both insects have scaled wings. The butterfly card shows clubbed antennae and upright resting wings, whereas the moth card shows feathery antennae and spread resting wings.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "frog_comparison:review:4",
          "teaching_block": "Compare the same feature for both subjects and replace opinions with details from the fact card. Retrieve the construct, then verify it against the passage. Use the visible passage to practise sentence comprehension and compare contrast; include both details.",
          "passage": "Crab card: hard outer shell, ten jointed legs, two claws. Turtle card: hard shell around the body, four legs, no claws listed. Both cards place the animals near water.",
          "prompt": "Write a factual comparison of shell, legs, and one shared setting detail.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_comparison:review:4:similarity",
              "description": "States the hard-shell and near-water similarities.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_comparison:review:4:differences",
              "description": "Contrasts leg counts and reports the claw evidence carefully.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_comparison:review:4:similarity",
              "description": "States the hard-shell and near-water similarities.",
              "any_of": [
                "hard shells near water"
              ]
            },
            {
              "id": "frog_comparison:review:4:differences",
              "description": "Contrasts leg counts and reports the claw evidence carefully.",
              "any_of": [
                "crab has ten jointed legs",
                "turtle has four legs",
                "no claws are listed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "cards",
            "describe",
            "animals"
          ],
          "model_answer": "Both cards describe animals with hard shells near water. The crab has ten jointed legs and two claws, while the turtle has four legs and no claws are listed on its card.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "one-sided-or-unmatched-comparison",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.compare_contrast"
          ],
          "misconception": "The learner lists a fact about only one animal, compares unrelated categories, or replaces evidence with a personal preference.",
          "remediation": "Use a two-column same-category chart, then write one both statement and one but/while statement from matched facts.",
          "support_check_ids": [
            "frog_comparison:support:bridge",
            "frog_comparison:support:masterclass",
            "frog_comparison:support:revision_level_1",
            "frog_comparison:support:revision_level_2",
            "frog_comparison:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "frog_comparison:support:bridge",
          "teaching_block": "Compare the same category across both animals and reject one-sided or unsupported statements. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "A fish remains in water; a frog can move between a bank and pond.",
          "prompt": "Which difference matches the card?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "the frog can use land and water",
            "the fish can fly",
            "the frog has fins",
            "both remain only in water"
          ],
          "accepted_answers": [
            "the frog can use land and water"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "frog_comparison:support:masterclass",
          "teaching_block": "Compare the same category across both animals and reject one-sided or unsupported statements. Reject any option that adds a fact the passage never gives.",
          "passage": "A duck has feathers and a bill; a frog has smooth skin and no feathers.",
          "prompt": "Which category is being compared?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "body covering",
            "time of day",
            "sound volume",
            "nest size"
          ],
          "accepted_answers": [
            "body covering"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "frog_comparison:support:revision_level_1",
          "teaching_block": "Compare the same category across both animals and reject one-sided or unsupported statements. Break the task into one smaller decision and check it carefully.",
          "passage": "A frog and toad are both amphibians in the supplied card.",
          "prompt": "What kind of comparison is this?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "a supported similarity",
            "an unsupported difference",
            "a sequence",
            "a cause"
          ],
          "accepted_answers": [
            "a supported similarity"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "frog_comparison:support:revision_level_2",
          "teaching_block": "Compare the same category across both animals and reject one-sided or unsupported statements. Name the rule first, then apply it to this new example.",
          "passage": "Frog: webbed back feet. Lizard: toes without webbing in the card.",
          "prompt": "Which sentence uses both facts?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "Both have identical feet.",
            "The frog has webbed back feet, but the lizard's toes lack webbing.",
            "The lizard swims with fins.",
            "The frog has feathers."
          ],
          "accepted_answers": [
            "The frog has webbed back feet, but the lizard's toes lack webbing."
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "frog_comparison:support:revision_level_3",
          "teaching_block": "Compare the same category across both animals and reject one-sided or unsupported statements. Compare the tempting error with the evidence that corrects it.",
          "passage": "Fish: fins and tail for swimming. Frog: paired legs for kicking in water.",
          "prompt": "Which comparison keeps the same category?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "their swimming body parts differ",
            "the frog is green and fish live in groups",
            "both are interesting",
            "fish have ponds"
          ],
          "accepted_answers": [
            "their swimming body parts differ"
          ]
        }
      }
    },
    {
      "level_id": "frog_calls_and_connectors",
      "title": "Connect frog ideas clearly",
      "focus": "choose connectors by addition, choice, contrast, and cause",
      "outcome": "Write complete connected sentences using and, or, but, and because according to the intended logical relationship.",
      "skill_ids": [
        "grammar.connectors_because_and_but",
        "writing.complete_sentence"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch05:learn:3-4"
      ],
      "connect": {
        "teaching_block": "Connectors are chosen by meaning: and adds, or offers alternatives, but marks contrast, and because introduces a reason.",
        "passage": "A frog may call from reeds or from a bank, and its throat pouch helps the call carry. The connector roles are different.",
        "prompt": "Continue when you can explain how this example helps you choose connectors by addition, choice, contrast, and cause."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "frog_calls_and_connectors:co_construct",
        "teaching_block": "Name the relationship between the clauses before choosing the connector. Locate the exact clue before comparing the choices.",
        "passage": "The frog swims easily ___ it has webbed feet.",
        "prompt": "Which connector gives the reason?",
        "skill_ids": [
          "grammar.connectors_because_and_but"
        ],
        "options": [
          "and",
          "or",
          "because",
          "but"
        ],
        "accepted_answers": [
          "because"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "frog_calls_and_connectors:guided:1",
          "teaching_block": "Name the relationship between the clauses before choosing the connector. Read the whole sentence, then test every option against its meaning.",
          "passage": "The frog can rest on the bank ___ enter the pond.",
          "prompt": "Which connector offers alternatives?",
          "skill_ids": [
            "grammar.connectors_because_and_but"
          ],
          "options": [
            "because",
            "but",
            "or",
            "so"
          ],
          "accepted_answers": [
            "or"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:guided:2",
          "teaching_block": "Write both complete ideas around the connector and verify that its logical role matches the meaning. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "The frog moves easily in water. It has webbed back feet.",
          "prompt": "Write one complete because sentence.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "result",
              "description": "Includes easy movement in water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Uses webbed back feet as the reason.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "result",
              "description": "Includes easy movement in water.",
              "any_of": [
                "moves easily in water"
              ]
            },
            {
              "id": "reason",
              "description": "Uses webbed back feet as the reason.",
              "any_of": [
                "because it has webbed",
                "because of webbed feet"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "moves",
            "easily",
            "water",
            "because",
            "webbed"
          ],
          "model_answer": "The frog moves easily in water because it has webbed back feet.",
          "pass_score": 0.8
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_calls_and_connectors:guided:3",
          "teaching_block": "Identify which fact explains the other, then place because immediately before the cause clause.",
          "passage": "The air became humid. The frogs began calling from the ditch.",
          "prompt": "Which sentence expresses the supplied cause clearly?",
          "skill_ids": [
            "grammar.connectors_because_and_but"
          ],
          "options": [
            "The frogs began calling because the air became humid.",
            "The air became humid but because the frogs.",
            "The frogs began calling and although the ditch.",
            "Because the frogs began, humid the air called."
          ],
          "accepted_answers": [
            "The frogs began calling because the air became humid."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_calls_and_connectors:guided:4",
          "teaching_block": "Use but when both facts are true and the second contrasts with an expectation raised by the first.",
          "passage": "The frog is small. Its call carries across the field.",
          "prompt": "Which sentence marks the contrast correctly?",
          "skill_ids": [
            "grammar.connectors_because_and_but"
          ],
          "options": [
            "The frog is small because its call carries across the field.",
            "The frog is small, but its call carries across the field.",
            "But the frog because small its call.",
            "The frog is small and because across the field."
          ],
          "accepted_answers": [
            "The frog is small, but its call carries across the field."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:independent:1",
          "teaching_block": "Write both complete ideas around the connector and verify that its logical role matches the meaning. Build the answer from two visible pieces of evidence.",
          "passage": "The frog enters the pond. The bank has become hot.",
          "prompt": "Join the ideas in one complete sentence using because.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "result",
              "description": "States that the frog enters the pond.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "cause",
              "description": "States that the bank is hot after because.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "result",
              "description": "States that the frog enters the pond.",
              "any_of": [
                "frog enters the pond"
              ]
            },
            {
              "id": "cause",
              "description": "States that the bank is hot after because.",
              "any_of": [
                "because the bank is hot",
                "because the bank became hot"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 9,
          "relevance_terms": [
            "frog",
            "enters",
            "pond",
            "because",
            "bank"
          ],
          "model_answer": "The frog enters the pond because the bank has become hot. Reference evidence states: because the bank is hot.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:independent:2",
          "teaching_block": "Write both complete ideas around the connector and verify that its logical role matches the meaning. State the relationship and support it with the relevant detail.",
          "passage": "A frog can call from the reeds. It can call from the muddy bank.",
          "prompt": "Join the alternatives with or in one complete sentence.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "first",
              "description": "Includes calling from the reeds.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "second",
              "description": "Includes calling from the bank as an alternative.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "first",
              "description": "Includes calling from the reeds.",
              "any_of": [
                "call from the reeds"
              ]
            },
            {
              "id": "second",
              "description": "Includes calling from the bank as an alternative.",
              "any_of": [
                "or from the bank",
                "or the muddy bank"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "call",
            "from",
            "reeds",
            "bank",
            "muddy"
          ],
          "model_answer": "A frog can call from the reeds or from the muddy bank. Reference evidence states: or from the bank.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:independent:3",
          "teaching_block": "Decide which clause answers why, then join the two complete ideas without reversing their relationship.",
          "passage": "The pond was hidden by tall grass. We located it by following the repeated croaks.",
          "prompt": "Join the ideas with because, keeping the cause and result accurate.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "result",
              "description": "Keeps locating the hidden pond as the result.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "cause",
              "description": "Places following the repeated croaks after because.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "result",
              "description": "Keeps locating the hidden pond as the result.",
              "any_of": [
                "located the hidden pond"
              ]
            },
            {
              "id": "cause",
              "description": "Places following the repeated croaks after because.",
              "any_of": [
                "because we followed the repeated croaks"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "pond",
            "hidden",
            "tall",
            "grass",
            "located",
            "following",
            "repeated",
            "croaks"
          ],
          "model_answer": "We located the hidden pond because we followed the repeated croaks through the tall grass.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "result",
            "cause"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:independent:4",
          "teaching_block": "Place but between the expectation and the surprising observation, with a comma before the connector.",
          "passage": "Ravi expected silence after sunset. A low chorus continued beside the pond.",
          "prompt": "Write one contrast sentence with but and preserve both facts.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "expectation",
              "description": "Keeps Ravi's expectation of silence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "contrast",
              "description": "Contrasts it with the continuing chorus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "expectation",
              "description": "Keeps Ravi's expectation of silence.",
              "any_of": [
                "expected silence after sunset"
              ]
            },
            {
              "id": "contrast",
              "description": "Contrasts it with the continuing chorus.",
              "any_of": [
                "but a low chorus continued"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 11,
          "relevance_terms": [
            "ravi",
            "expected",
            "silence",
            "after",
            "sunset",
            "chorus",
            "continued",
            "beside"
          ],
          "model_answer": "Ravi expected silence after sunset, but a low chorus continued beside the pond.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "expectation",
            "contrast"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:transfer:1",
          "teaching_block": "Write both complete ideas around the connector and verify that its logical role matches the meaning. Explain the first part before connecting it to the result.",
          "passage": "The lane was noisy. The myna's whistle remained clear.",
          "prompt": "Join the contrast with but.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "noise",
              "description": "States that the lane was noisy.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "clear",
              "description": "Contrasts that the whistle remained clear.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "noise",
              "description": "States that the lane was noisy.",
              "any_of": [
                "lane was noisy"
              ]
            },
            {
              "id": "clear",
              "description": "Contrasts that the whistle remained clear.",
              "any_of": [
                "but the whistle remained clear",
                "whistle was clear"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 9,
          "relevance_terms": [
            "lane",
            "noisy",
            "whistle",
            "remained",
            "clear"
          ],
          "model_answer": "The lane was noisy, but the myna's whistle remained clear. Reference evidence states: but the whistle remained clear.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:transfer:2",
          "teaching_block": "Write both complete ideas around the connector and verify that its logical role matches the meaning. Use your own words while preserving every required idea.",
          "passage": "The frog has webbed feet. It has long hind legs.",
          "prompt": "Join the two related features with and.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "webbing",
              "description": "Includes webbed feet.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "legs",
              "description": "Adds long hind legs.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "webbing",
              "description": "Includes webbed feet.",
              "any_of": [
                "webbed feet"
              ]
            },
            {
              "id": "legs",
              "description": "Adds long hind legs.",
              "any_of": [
                "and long hind legs"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "webbed",
            "feet",
            "long",
            "hind",
            "legs"
          ],
          "model_answer": "The frog has webbed feet and long hind legs.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:transfer:3",
          "teaching_block": "Transfer both connector roles to the same event while keeping contrast separate from cause.",
          "passage": "The path looked dry. The ranger closed it after finding fragile frog eggs in a shallow rut.",
          "prompt": "Write two linked sentences: one with but for contrast and one with because for the reason.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "contrast",
              "description": "Uses but to contrast appearance with closure.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Uses because to give the egg-protection reason.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "contrast",
              "description": "Uses but to contrast appearance with closure.",
              "any_of": [
                "looked dry, but the ranger closed it"
              ]
            },
            {
              "id": "reason",
              "description": "Uses because to give the egg-protection reason.",
              "any_of": [
                "because fragile frog eggs lay"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "path",
            "looked",
            "ranger",
            "closed",
            "after",
            "finding",
            "fragile",
            "frog"
          ],
          "model_answer": "The path looked dry, but the ranger closed it. She closed it because fragile frog eggs lay in a shallow rut.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "contrast",
            "reason"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:transfer:4",
          "teaching_block": "Choose a connector for the intended relationship and write complete ideas on both sides of it. Apply the same construct to this new passage. Use the visible passage to practise connectors because and but and complete sentence; include both details.",
          "passage": "The pond looked still. Small circles spread across its surface. A frog had just entered the water.",
          "prompt": "Write one complete sentence with but for the appearance contrast and one with because for the cause.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_calls_and_connectors:transfer:4:contrast",
              "description": "Uses but between two complete contrasting ideas.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_calls_and_connectors:transfer:4:cause",
              "description": "Uses because to connect the circles with the frog's entry.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_calls_and_connectors:transfer:4:contrast",
              "description": "Uses but between two complete contrasting ideas.",
              "any_of": [
                "looked still, but small circles spread"
              ]
            },
            {
              "id": "frog_calls_and_connectors:transfer:4:cause",
              "description": "Uses because to connect the circles with the frog's entry.",
              "any_of": [
                "circles appeared because",
                "frog had just entered"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "looked",
            "still",
            "small"
          ],
          "model_answer": "The pond looked still, but small circles spread across its surface. The circles appeared because a frog had just entered the water.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:review:1",
          "teaching_block": "Write both complete ideas around the connector and verify that its logical role matches the meaning. Apply the same reasoning to a different setting and justify it.",
          "passage": "A lizard stayed still against the bark. A bird was circling overhead.",
          "prompt": "Write a complete because sentence that makes the reason clear.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "action",
              "description": "States that the lizard stayed still.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Uses the circling bird as the reason.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "action",
              "description": "States that the lizard stayed still.",
              "any_of": [
                "lizard stayed still"
              ]
            },
            {
              "id": "reason",
              "description": "Uses the circling bird as the reason.",
              "any_of": [
                "because a bird was circling",
                "because the bird circled overhead"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 11,
          "relevance_terms": [
            "lizard",
            "stayed",
            "still",
            "because",
            "bird"
          ],
          "model_answer": "The lizard stayed still against the bark because a bird was circling overhead.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:review:2",
          "teaching_block": "Write both complete ideas around the connector and verify that its logical role matches the meaning. Separate what is stated from what can reasonably be inferred.",
          "passage": "A duck can paddle in the pool. It can rest on the bank. Its feathers remain visible in both places.",
          "prompt": "Use or for the alternative places and and for the added fact.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "alternatives",
              "description": "Uses or between pool and bank actions.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "addition",
              "description": "Uses and to add the feather fact.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "alternatives",
              "description": "Uses or between pool and bank actions.",
              "any_of": [
                "paddle in the pool or rest",
                "pool or bank"
              ]
            },
            {
              "id": "addition",
              "description": "Uses and to add the feather fact.",
              "any_of": [
                "and its feathers",
                "and feathers remain visible"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 17,
          "relevance_terms": [
            "paddle",
            "pool",
            "rest",
            "bank",
            "feathers"
          ],
          "model_answer": "A duck can paddle in the pool or rest on the bank, and its feathers remain visible in both places.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:review:3",
          "teaching_block": "Choose a connector for the intended relationship and write complete ideas on both sides of it. Retrieve the construct, then verify it against the passage. Use the visible passage to practise connectors because and but and complete sentence; include both details.",
          "passage": "The boardwalk was open in the morning. Rangers closed it at noon. Heavy rain had covered the lowest section.",
          "prompt": "Combine the facts with but and because in two complete connected sentences.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_calls_and_connectors:review:3:but",
              "description": "Uses but to show the change from open to closed.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_calls_and_connectors:review:3:because",
              "description": "Uses because for the rain-covered-section reason.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_calls_and_connectors:review:3:but",
              "description": "Uses but to show the change from open to closed.",
              "any_of": [
                "open in the morning, but rangers closed"
              ]
            },
            {
              "id": "frog_calls_and_connectors:review:3:because",
              "description": "Uses because for the rain-covered-section reason.",
              "any_of": [
                "closed it because heavy rain",
                "covered the lowest section"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "boardwalk",
            "morning",
            "rangers"
          ],
          "model_answer": "The boardwalk was open in the morning, but rangers closed it at noon. They closed it because heavy rain had covered the lowest section.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "frog_calls_and_connectors:review:4",
          "teaching_block": "Choose a connector for the intended relationship and write complete ideas on both sides of it. Retrieve the construct, then verify it against the passage. Use the visible passage to practise connectors because and but and complete sentence; include both details.",
          "passage": "You may observe the pond from the bridge. You may sit at the marked bench. You must keep the path clear.",
          "prompt": "Use or for the two alternatives and and to add the path rule in one complete sentence.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_calls_and_connectors:review:4:choice",
              "description": "Uses or between the two allowed observation places.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_calls_and_connectors:review:4:addition",
              "description": "Uses and to attach the complete path rule.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_calls_and_connectors:review:4:choice",
              "description": "Uses or between the two allowed observation places.",
              "any_of": [
                "from the bridge or sit",
                "marked bench"
              ]
            },
            {
              "id": "frog_calls_and_connectors:review:4:addition",
              "description": "Uses and to attach the complete path rule.",
              "any_of": [
                "and you must keep the path clear"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "observe",
            "bridge",
            "marked"
          ],
          "model_answer": "You may observe the pond from the bridge or sit at the marked bench, and you must keep the path clear.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "connector-chosen-by-sound",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.complete_sentence"
          ],
          "misconception": "The learner chooses a connector because it sounds familiar, leaving the clause relationship wrong or one side incomplete.",
          "remediation": "Label the relationship as add, choice, contrast, or reason before joining two complete idea cards with the matching connector.",
          "support_check_ids": [
            "frog_calls_and_connectors:support:bridge",
            "frog_calls_and_connectors:support:masterclass",
            "frog_calls_and_connectors:support:revision_level_1",
            "frog_calls_and_connectors:support:revision_level_2",
            "frog_calls_and_connectors:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "frog_calls_and_connectors:support:bridge",
          "teaching_block": "Name the relationship between the clauses before choosing the connector. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "The frog has long hind legs ___ webbed back feet.",
          "prompt": "Which connector adds a related feature?",
          "skill_ids": [
            "grammar.connectors_because_and_but"
          ],
          "options": [
            "or",
            "and",
            "but",
            "because"
          ],
          "accepted_answers": [
            "and"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "frog_calls_and_connectors:support:masterclass",
          "teaching_block": "Name the relationship between the clauses before choosing the connector. Reject any option that adds a fact the passage never gives.",
          "passage": "A shadow passed, ___ the frog slipped under a root.",
          "prompt": "Which connector can join the cause and response?",
          "skill_ids": [
            "grammar.connectors_because_and_but"
          ],
          "options": [
            "because",
            "so",
            "or",
            "but"
          ],
          "accepted_answers": [
            "so"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "frog_calls_and_connectors:support:revision_level_1",
          "teaching_block": "Name the relationship between the clauses before choosing the connector. Break the task into one smaller decision and check it carefully.",
          "passage": "The frog may hide among leaves ___ beneath a ledge.",
          "prompt": "Which word shows a choice of places?",
          "skill_ids": [
            "grammar.connectors_because_and_but"
          ],
          "options": [
            "or",
            "because",
            "and",
            "but"
          ],
          "accepted_answers": [
            "or"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "frog_calls_and_connectors:support:revision_level_2",
          "teaching_block": "Name the relationship between the clauses before choosing the connector. Name the rule first, then apply it to this new example.",
          "passage": "The frog is small, ___ its call carries across the pond.",
          "prompt": "Which connector shows contrast?",
          "skill_ids": [
            "grammar.connectors_because_and_but"
          ],
          "options": [
            "because",
            "and",
            "or",
            "but"
          ],
          "accepted_answers": [
            "but"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "frog_calls_and_connectors:support:revision_level_3",
          "teaching_block": "Name the relationship between the clauses before choosing the connector. Compare the tempting error with the evidence that corrects it.",
          "passage": "The throat pouch vibrates ___ the call grows louder.",
          "prompt": "Which connector simply adds the next related fact?",
          "skill_ids": [
            "grammar.connectors_because_and_but"
          ],
          "options": [
            "and",
            "or",
            "because",
            "but"
          ],
          "accepted_answers": [
            "and"
          ]
        }
      }
    },
    {
      "level_id": "frog_sentence_sequence",
      "title": "Build natural sentence order",
      "focus": "arrange subject, verb, detail, and adverb clearly",
      "outcome": "Reconstruct a complete English sentence and place an adverb where its timing, frequency, or manner relationship is clear.",
      "skill_ids": [
        "grammar.sentence_order",
        "grammar.adverbs"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch05:learn:3-4"
      ],
      "connect": {
        "teaching_block": "A clear sentence usually places the subject before its verb, keeps the object or place with the action, and positions an adverb beside the idea it modifies.",
        "passage": "The frog quickly crosses the wet path at night. The subject, action, manner, place, and time each have a readable role.",
        "prompt": "Continue when you can explain how this example helps you arrange subject, verb, detail, and adverb clearly."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "frog_sentence_sequence:co_construct",
        "teaching_block": "Find the subject and verb first, then place the adverb next to the action or time relationship it describes. Locate the exact clue before comparing the choices.",
        "passage": "words: frog / the / catches / an insect",
        "prompt": "Which arrangement is complete?",
        "skill_ids": [
          "grammar.sentence_order",
          "grammar.adverbs"
        ],
        "options": [
          "The frog catches an insect.",
          "The catches frog an insect.",
          "Frog the an insect catches.",
          "The frog an catches insect."
        ],
        "accepted_answers": [
          "The frog catches an insect."
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:guided:1",
          "teaching_block": "Find the subject and verb first, then place the adverb next to the action or time relationship it describes. Read the whole sentence, then test every option against its meaning.",
          "passage": "words: silently / waits / crocodile / the / near the bank",
          "prompt": "Which sentence has natural order?",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "options": [
            "Silently the near waits crocodile bank.",
            "The crocodile waits silently near the bank.",
            "The waits crocodile near silently bank.",
            "Near waits the bank crocodile silently."
          ],
          "accepted_answers": [
            "The crocodile waits silently near the bank."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:guided:2",
          "teaching_block": "Find the subject and verb first, then place the adverb next to the action or time relationship it describes. Track who or what each detail belongs to before deciding.",
          "passage": "The frog ___ visits the pond after rain. It does so on most rainy evenings.",
          "prompt": "Which frequency adverb fits?",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "options": [
            "carefully",
            "often",
            "outside",
            "yesterday"
          ],
          "accepted_answers": [
            "often"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:guided:3",
          "teaching_block": "Build subject plus verb first, then place the manner adverb close to the action and finish with the place phrase.",
          "passage": "Notes: quietly / the froglet / moved / beneath the fern",
          "prompt": "Which sentence has correct order and adverb placement?",
          "skill_ids": [
            "grammar.sentence_order"
          ],
          "options": [
            "Quietly beneath moved the froglet fern.",
            "The moved froglet beneath quietly fern.",
            "Beneath the quietly froglet moved fern.",
            "The froglet moved quietly beneath the fern."
          ],
          "accepted_answers": [
            "The froglet moved quietly beneath the fern."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:guided:4",
          "teaching_block": "Keep the subject and verb together, attach loudly to called, and place the time phrase at a clear boundary.",
          "passage": "Notes: after the shower / loudly / several frogs / called",
          "prompt": "Which version forms a clear complete sentence?",
          "skill_ids": [
            "grammar.adverbs"
          ],
          "options": [
            "Several frogs called loudly after the shower.",
            "After called several loudly the frogs shower.",
            "Several loudly after frogs the shower called.",
            "Called the shower frogs several after loudly."
          ],
          "accepted_answers": [
            "Several frogs called loudly after the shower."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:independent:1",
          "teaching_block": "Rebuild every supplied part into a natural sentence and explain what the adverb tells the reader. Build the answer from two visible pieces of evidence.",
          "passage": "words: across the pond / quickly / the frog / swims",
          "prompt": "Arrange every part into one natural sentence and state what quickly describes.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "sentence",
              "description": "Writes a natural complete sentence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "adverb",
              "description": "States that quickly describes how the frog swims.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sentence",
              "description": "Writes a natural complete sentence.",
              "any_of": [
                "The frog swims quickly across the pond",
                "The frog quickly swims across the pond"
              ]
            },
            {
              "id": "adverb",
              "description": "States that quickly describes how the frog swims.",
              "any_of": [
                "describes how it swims",
                "manner of swimming"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "frog",
            "swims",
            "quickly",
            "across",
            "pond"
          ],
          "model_answer": "The frog swims quickly across the pond. Quickly describes how it swims.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:independent:2",
          "teaching_block": "Rebuild every supplied part into a natural sentence and explain what the adverb tells the reader. State the relationship and support it with the relevant detail.",
          "passage": "words: after rain / often / frogs / call / near the drain",
          "prompt": "Build a complete sentence and identify what often tells the reader.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "sentence",
              "description": "Orders all parts naturally.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frequency",
              "description": "Explains that often tells how frequently.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sentence",
              "description": "Orders all parts naturally.",
              "any_of": [
                "Frogs often call near the drain after rain"
              ]
            },
            {
              "id": "frequency",
              "description": "Explains that often tells how frequently.",
              "any_of": [
                "how frequently",
                "how often they call"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 13,
          "relevance_terms": [
            "frogs",
            "often",
            "call",
            "near",
            "drain"
          ],
          "model_answer": "Frogs often call near the drain after rain. Often tells how frequently the calling happens.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:independent:3",
          "teaching_block": "Assemble the subject-verb-object core first, then place the manner and location details where their meanings stay clear.",
          "passage": "Word tiles: carefully / the children / beside the pond / recorded / each call",
          "prompt": "Arrange every tile into one complete sentence and explain where the adverb belongs.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "sentence",
              "description": "Uses every tile in a grammatical sentence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "placement",
              "description": "Explains that carefully modifies recorded.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sentence",
              "description": "Uses every tile in a grammatical sentence.",
              "any_of": [
                "children carefully recorded each call"
              ]
            },
            {
              "id": "placement",
              "description": "Explains that carefully modifies recorded.",
              "any_of": [
                "carefully belongs beside recorded"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "word",
            "tiles",
            "carefully",
            "children",
            "beside",
            "pond",
            "recorded",
            "each"
          ],
          "model_answer": "The children carefully recorded each call beside the pond. Carefully belongs beside recorded because it tells how they performed the action.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:independent:4",
          "teaching_block": "Protect the subject-verb-object core, then attach the place and time phrases without splitting the action.",
          "passage": "Draft: Near the reeds the watcher suddenly heard after dusk a splash.",
          "prompt": "Rewrite the draft for natural order while keeping place, manner, time, and event.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Keeps watcher, heard, and splash together.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "details",
              "description": "Retains the reeds and dusk details clearly.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Keeps watcher, heard, and splash together.",
              "any_of": [
                "watcher suddenly heard a splash"
              ]
            },
            {
              "id": "details",
              "description": "Retains the reeds and dusk details clearly.",
              "any_of": [
                "near the reeds after dusk"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "draft",
            "near",
            "reeds",
            "watcher",
            "suddenly",
            "heard",
            "after",
            "dusk"
          ],
          "model_answer": "The watcher suddenly heard a splash near the reeds after dusk.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:transfer:1",
          "teaching_block": "Rebuild every supplied part into a natural sentence and explain what the adverb tells the reader. Explain the first part before connecting it to the result.",
          "passage": "parts: the heron / steps / slowly / through shallow water",
          "prompt": "Write the sentence and explain slowly.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "order",
              "description": "Uses subject-verb-adverb-place order naturally.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "manner",
              "description": "Explains that slowly describes the manner of stepping.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "order",
              "description": "Uses subject-verb-adverb-place order naturally.",
              "any_of": [
                "The heron steps slowly through shallow water"
              ]
            },
            {
              "id": "manner",
              "description": "Explains that slowly describes the manner of stepping.",
              "any_of": [
                "how the heron steps",
                "manner of movement"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "heron",
            "steps",
            "slowly",
            "through",
            "shallow"
          ],
          "model_answer": "The heron steps slowly through shallow water. Slowly describes how the heron steps.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:transfer:2",
          "teaching_block": "Rebuild every supplied part into a natural sentence and explain what the adverb tells the reader. Use your own words while preserving every required idea.",
          "passage": "parts: tomorrow / our class / will observe / the pond / quietly",
          "prompt": "Arrange the sentence and distinguish the time and manner adverbs.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "sentence",
              "description": "Uses every part in a natural sentence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "time",
              "description": "Identifies tomorrow as time.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "manner",
              "description": "Identifies quietly as manner.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sentence",
              "description": "Uses every part in a natural sentence.",
              "any_of": [
                "Our class will observe the pond quietly tomorrow",
                "Tomorrow our class will observe"
              ]
            },
            {
              "id": "time",
              "description": "Identifies tomorrow as time.",
              "any_of": [
                "tomorrow tells when",
                "time adverb"
              ]
            },
            {
              "id": "manner",
              "description": "Identifies quietly as manner.",
              "any_of": [
                "quietly tells how",
                "manner adverb"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "class",
            "will",
            "observe",
            "pond",
            "quietly"
          ],
          "model_answer": "Our class will observe the pond quietly tomorrow. Tomorrow tells when, while quietly tells how.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:transfer:3",
          "teaching_block": "Transfer sentence assembly to a new animal observation and justify the manner-adverb placement.",
          "passage": "Field notes: patiently / a heron / at the water's edge / waited / all morning",
          "prompt": "Create one natural sentence, then identify which word tells how the heron waited.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "sentence",
              "description": "Forms a natural sentence from every note.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "adverb",
              "description": "Identifies patiently as describing how it waited.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sentence",
              "description": "Forms a natural sentence from every note.",
              "any_of": [
                "heron waited patiently at the water's edge"
              ]
            },
            {
              "id": "adverb",
              "description": "Identifies patiently as describing how it waited.",
              "any_of": [
                "patiently tells how the heron waited"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 17,
          "relevance_terms": [
            "field",
            "notes",
            "patiently",
            "heron",
            "water's",
            "edge",
            "waited",
            "morning"
          ],
          "model_answer": "A heron waited patiently at the water's edge all morning. The word patiently tells how the heron waited.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:transfer:4",
          "teaching_block": "Build a natural English sentence, then place and explain each time, frequency, or manner adverb. Apply the same construct to this new passage. Use the visible passage to practise sentence order and adverbs; include both details.",
          "passage": "parts: after sunset / the tree frogs / often / call / from the wet hedge / loudly",
          "prompt": "Arrange a natural sentence, then identify the time, frequency, and manner information.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_sentence_sequence:transfer:4:sentence",
              "description": "Builds the complete sentence in natural order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_sentence_sequence:transfer:4:adverbs",
              "description": "Explains the time, frequency, and manner information.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_sentence_sequence:transfer:4:sentence",
              "description": "Builds the complete sentence in natural order.",
              "any_of": [
                "After sunset, the tree frogs often call loudly"
              ]
            },
            {
              "id": "frog_sentence_sequence:transfer:4:adverbs",
              "description": "Explains the time, frequency, and manner information.",
              "any_of": [
                "tells when",
                "tells frequency",
                "tells how they call"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "sunset",
            "frogs",
            "often"
          ],
          "model_answer": "After sunset, the tree frogs often call loudly from the wet hedge. After sunset tells when, often tells frequency, and loudly tells how they call.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_sentence_sequence:transfer:4:sentence",
            "frog_sentence_sequence:transfer:4:adverbs"
          ]
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:review:1",
          "teaching_block": "Rebuild every supplied part into a natural sentence and explain what the adverb tells the reader. Apply the same reasoning to a different setting and justify it.",
          "passage": "parts: the frog / waited / patiently / under a leaf / until dusk",
          "prompt": "Rebuild the sentence and explain which word describes manner.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "sentence",
              "description": "Orders all sentence parts naturally.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "manner",
              "description": "Identifies patiently as describing how it waited.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sentence",
              "description": "Orders all sentence parts naturally.",
              "any_of": [
                "The frog waited patiently under a leaf until dusk"
              ]
            },
            {
              "id": "manner",
              "description": "Identifies patiently as describing how it waited.",
              "any_of": [
                "patiently describes how",
                "manner is patiently"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 13,
          "relevance_terms": [
            "frog",
            "waited",
            "patiently",
            "under",
            "leaf"
          ],
          "model_answer": "The frog waited patiently under a leaf until dusk. Patiently describes how it waited.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:review:2",
          "teaching_block": "Rebuild every supplied part into a natural sentence and explain what the adverb tells the reader. Separate what is stated from what can reasonably be inferred.",
          "passage": "A learner writes: 'Carefully the across frog stone jumped.'",
          "prompt": "Repair the order and explain where carefully belongs.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "repair",
              "description": "Writes a natural repaired sentence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "placement",
              "description": "Explains that carefully stays near jumped because it describes the action.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "repair",
              "description": "Writes a natural repaired sentence.",
              "any_of": [
                "The frog jumped carefully across the stone",
                "The frog carefully jumped across the stone"
              ]
            },
            {
              "id": "placement",
              "description": "Explains that carefully stays near jumped because it describes the action.",
              "any_of": [
                "near the verb",
                "describes how it jumped"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "frog",
            "jumped",
            "carefully",
            "across",
            "stone"
          ],
          "model_answer": "The frog jumped carefully across the stone. Carefully stays near jumped because it describes how the action happened. Reference evidence states: near the verb.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:review:3",
          "teaching_block": "Build a natural English sentence, then place and explain each time, frequency, or manner adverb. Retrieve the construct, then verify it against the passage. Use the visible passage to practise sentence order and adverbs; include both details.",
          "passage": "parts: the pond monitor / carefully / records / each water level / every Friday",
          "prompt": "Rebuild the sentence and explain which phrase tells when and which word tells how.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_sentence_sequence:review:3:order",
              "description": "Writes the supplied parts in natural English order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_sentence_sequence:review:3:roles",
              "description": "Distinguishes the time phrase from the manner adverb.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_sentence_sequence:review:3:order",
              "description": "Writes the supplied parts in natural English order.",
              "any_of": [
                "pond monitor carefully records",
                "every Friday"
              ]
            },
            {
              "id": "frog_sentence_sequence:review:3:roles",
              "description": "Distinguishes the time phrase from the manner adverb.",
              "any_of": [
                "Every Friday tells when",
                "carefully tells how"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "monitor",
            "carefully",
            "records"
          ],
          "model_answer": "The pond monitor carefully records each water level every Friday. Every Friday tells when the recording happens, and carefully tells how it is done.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_sentence_sequence:review:3:order",
            "frog_sentence_sequence:review:3:roles"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_sentence_sequence:review:4",
          "teaching_block": "Build a natural English sentence, then place and explain each time, frequency, or manner adverb. Retrieve the construct, then verify it against the passage. Use the visible passage to practise sentence order and adverbs; include both details.",
          "passage": "A learner writes: 'Near the reeds silently waited yesterday the heron.'",
          "prompt": "Repair the order and explain the jobs of yesterday and silently.",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "frog_sentence_sequence:review:4:repair",
              "description": "Produces a natural complete sentence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_sentence_sequence:review:4:explain",
              "description": "Identifies the time and manner information.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_sentence_sequence:review:4:repair",
              "description": "Produces a natural complete sentence.",
              "any_of": [
                "Yesterday, the heron waited silently near the reeds"
              ]
            },
            {
              "id": "frog_sentence_sequence:review:4:explain",
              "description": "Identifies the time and manner information.",
              "any_of": [
                "Yesterday tells when",
                "silently tells how"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "yesterday",
            "heron",
            "waited"
          ],
          "model_answer": "Yesterday, the heron waited silently near the reeds. Yesterday tells when the waiting happened, while silently tells how the heron waited.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_sentence_sequence:review:4:repair",
            "frog_sentence_sequence:review:4:explain"
          ]
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "word-bag-or-adverb-misplacement",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "misconception": "The learner keeps all supplied words but ignores subject-verb order, or places an adverb where its target action is unclear.",
          "remediation": "Build the subject and verb spine first, attach object/place/time, then move the adverb beside the exact action or relationship it modifies.",
          "support_check_ids": [
            "frog_sentence_sequence:support:bridge",
            "frog_sentence_sequence:support:masterclass",
            "frog_sentence_sequence:support:revision_level_1",
            "frog_sentence_sequence:support:revision_level_2",
            "frog_sentence_sequence:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:support:bridge",
          "teaching_block": "Find the subject and verb first, then place the adverb next to the action or time relationship it describes. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "The frog moved ___ across the slippery stone.",
          "prompt": "Which manner adverb fits?",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "options": [
            "tomorrow",
            "nearby",
            "carefully",
            "weekly"
          ],
          "accepted_answers": [
            "carefully"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:support:masterclass",
          "teaching_block": "Find the subject and verb first, then place the adverb next to the action or time relationship it describes. Reject any option that adds a fact the passage never gives.",
          "passage": "words: turtle / a / slowly / swims / in the pool",
          "prompt": "Which sentence is correct?",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "options": [
            "A turtle swims slowly in the pool.",
            "A slowly turtle in swims pool.",
            "Swims a turtle the slowly pool.",
            "The pool turtle slowly a swims."
          ],
          "accepted_answers": [
            "A turtle swims slowly in the pool."
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:support:revision_level_1",
          "teaching_block": "Find the subject and verb first, then place the adverb next to the action or time relationship it describes. Break the task into one smaller decision and check it carefully.",
          "passage": "The class will visit the pond ___.",
          "prompt": "Which time adverb fits a future plan?",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "options": [
            "carefully",
            "tomorrow",
            "softly",
            "outside"
          ],
          "accepted_answers": [
            "tomorrow"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:support:revision_level_2",
          "teaching_block": "Find the subject and verb first, then place the adverb next to the action or time relationship it describes. Name the rule first, then apply it to this new example.",
          "passage": "The children looked ___ for the hidden frogs in the picture.",
          "prompt": "Which manner adverb best fits?",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "options": [
            "yesterday",
            "near",
            "carefully",
            "weekly"
          ],
          "accepted_answers": [
            "carefully"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "frog_sentence_sequence:support:revision_level_3",
          "teaching_block": "Find the subject and verb first, then place the adverb next to the action or time relationship it describes. Compare the tempting error with the evidence that corrects it.",
          "passage": "words: at night / hunts / the tiger / silently",
          "prompt": "Which order is natural?",
          "skill_ids": [
            "grammar.sentence_order",
            "grammar.adverbs"
          ],
          "options": [
            "At night silently the tiger hunts.",
            "The tiger hunts silently at night.",
            "Hunts at tiger night the silently.",
            "The silently at night hunts tiger."
          ],
          "accepted_answers": [
            "The tiger hunts silently at night."
          ]
        }
      }
    },
    {
      "level_id": "frog_friendly_reply",
      "title": "Reply to a pond-side friend",
      "focus": "answer, add a relevant detail, ask, and close",
      "outcome": "Write a coherent friendly message that responds to the sender, adds relevant information, asks one connected question, and closes politely.",
      "skill_ids": [
        "reading.sentence_comprehension",
        "writing.friendly_message",
        "writing.complete_sentence"
      ],
      "episode_kind": "expression_workshop",
      "source_anchor_ids": [
        "eng_c5_ch05:write:7"
      ],
      "companion_source_anchor_ids": [
        "eng_c5_ch05:speak:4-5",
        "eng_c5_ch05:listen:5-6"
      ],
      "connect": {
        "teaching_block": "A useful reply reads the sender's actual question, answers it directly, adds a connected detail, continues the exchange, and closes with the writer's name.",
        "passage": "Message: 'I heard frogs after rain. Do they visit near your home?' A direct reply must answer that question before changing topics.",
        "prompt": "Continue when you can explain how this example helps you answer, add a relevant detail, ask, and close."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "frog_friendly_reply:co_construct",
        "teaching_block": "Use the sender's question and details to identify the reply that stays relevant. Locate the exact clue before comparing the choices.",
        "passage": "Kabir asks whether tadpoles near your pond have changed.",
        "prompt": "Which opening responds directly?",
        "skill_ids": [
          "reading.sentence_comprehension"
        ],
        "options": [
          "Hi Kabir, I noticed tiny legs yesterday.",
          "Hi Kabir, our maths class was long.",
          "Hello Tara, I bought a book.",
          "Hi Kabir, ponds are blue in pictures."
        ],
        "accepted_answers": [
          "Hi Kabir, I noticed tiny legs yesterday."
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "frog_friendly_reply:guided:1",
          "teaching_block": "Use the sender's question and details to identify the reply that stays relevant. Read the whole sentence, then test every option against its meaning.",
          "passage": "Maya asks whether frogs visit after rain.",
          "prompt": "Which sentence answers her question?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "Rain can be loud.",
            "Yes, I sometimes see frogs near the drain after rain.",
            "My school has a library.",
            "Frogs are in Chapter 5."
          ],
          "accepted_answers": [
            "Yes, I sometimes see frogs near the drain after rain."
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:guided:2",
          "teaching_block": "Write a complete message with greeting, direct response, relevant detail, connected question, closing, and name. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "Maya asks, 'Do frogs visit near your home after rain?'",
          "prompt": "Write a greeting, direct one-sentence answer, and one related question.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "greeting",
              "description": "Greets Maya.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "answer",
              "description": "Directly answers the visit question in a complete sentence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "question",
              "description": "Asks one rain/frog question.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "greeting",
              "description": "Greets Maya.",
              "any_of": [
                "Hi Maya",
                "Dear Maya"
              ]
            },
            {
              "id": "answer",
              "description": "Directly answers the visit question in a complete sentence.",
              "any_of": [
                "frogs visit",
                "I have not seen frogs"
              ]
            },
            {
              "id": "question",
              "description": "Asks one rain/frog question.",
              "any_of": [
                "where did you see",
                "when do they visit"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 17,
          "relevance_terms": [
            "maya",
            "dear",
            "frogs",
            "visit",
            "have"
          ],
          "model_answer": "Hi Maya, frogs sometimes visit the drain near my home after rain. Where do you usually see them? Reference evidence states: frogs visit; where did you see.",
          "pass_score": 0.8
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_friendly_reply:guided:3",
          "teaching_block": "Locate the sender's real question, answer it directly, and add only a relevant detail from the message context.",
          "passage": "Message from Tara: 'I saw tadpoles near the bridge. Do you know why the water was fenced off?'",
          "prompt": "Which reply answers the question and adds one useful supplied detail?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "That is nice. I have nothing else to say.",
            "The bridge is certainly the oldest in the world.",
            "The ranger fenced the water to protect the tadpoles. A sign also asks visitors to stay on the path.",
            "Why are you asking me about a completely different park?"
          ],
          "accepted_answers": [
            "The ranger fenced the water to protect the tadpoles. A sign also asks visitors to stay on the path."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_friendly_reply:guided:4",
          "teaching_block": "A complete reply acknowledges both requests and may ask one practical follow-up question.",
          "passage": "Message from Kabir: 'Our class is counting frog calls on Friday. Can you bring a pencil and arrive by 6 p.m.?'",
          "prompt": "Which reply is complete and friendly?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "Friday frogs pencil maybe.",
            "I will arrive whenever I want and bring nothing.",
            "The pond contains exactly one thousand frogs.",
            "Yes, I can bring a pencil and arrive by 6 p.m. Where should I meet the class?"
          ],
          "accepted_answers": [
            "Yes, I can bring a pencil and arrive by 6 p.m. Where should I meet the class?"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:independent:1",
          "teaching_block": "Write a complete message with greeting, direct response, relevant detail, connected question, closing, and name. Build the answer from two visible pieces of evidence.",
          "passage": "Hi! I saw three tadpoles near the pond steps. Have you noticed any changes near your pond? - Kabir",
          "prompt": "Write Kabir a 35 to 55 word reply with every message part.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "greeting",
              "description": "Greets Kabir.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "answer",
              "description": "Answers whether changes were noticed.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "detail",
              "description": "Adds one relevant pond detail.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "question",
              "description": "Asks one connected question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "closing",
              "description": "Includes a closing and writer name.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "greeting",
              "description": "Greets Kabir.",
              "any_of": [
                "Hi Kabir",
                "Dear Kabir"
              ]
            },
            {
              "id": "answer",
              "description": "Answers whether changes were noticed.",
              "any_of": [
                "I noticed",
                "I have not noticed"
              ]
            },
            {
              "id": "detail",
              "description": "Adds one relevant pond detail.",
              "any_of": [
                "tiny legs",
                "near the pond",
                "after rain"
              ]
            },
            {
              "id": "question",
              "description": "Asks one connected question.",
              "any_of": [
                "did you notice",
                "when did you see"
              ]
            },
            {
              "id": "closing",
              "description": "Includes a closing and writer name.",
              "any_of": [
                "Your friend",
                "Best wishes"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "kabir",
            "dear",
            "noticed",
            "have",
            "tiny"
          ],
          "model_answer": "Hi Kabir, I noticed tiny back legs on two tadpoles near our pond yesterday. They stayed close to the shallow edge. Did the tadpoles near your steps have legs too? Your friend, Riya Reference evidence states: tiny legs; did you notice.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:independent:2",
          "teaching_block": "Write a complete message with greeting, direct response, relevant detail, connected question, closing, and name. State the relationship and support it with the relevant detail.",
          "passage": "Hello! A frog hid among the leaves in our rain garden today. Do frogs visit your school? - Arjun",
          "prompt": "Write a 35 to 55 word direct and friendly reply.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "greeting",
              "description": "Greets Arjun.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "answer",
              "description": "Directly answers the school-visit question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "detail",
              "description": "Adds one relevant observation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "question",
              "description": "Asks Arjun a related question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "closing",
              "description": "Closes with the writer's name.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "greeting",
              "description": "Greets Arjun.",
              "any_of": [
                "Hi Arjun",
                "Dear Arjun"
              ]
            },
            {
              "id": "answer",
              "description": "Directly answers the school-visit question.",
              "any_of": [
                "frogs visit",
                "I have not seen frogs"
              ]
            },
            {
              "id": "detail",
              "description": "Adds one relevant observation.",
              "any_of": [
                "after rain",
                "near the drain",
                "among plants"
              ]
            },
            {
              "id": "question",
              "description": "Asks Arjun a related question.",
              "any_of": [
                "what colour",
                "did it move",
                "where exactly"
              ]
            },
            {
              "id": "closing",
              "description": "Closes with the writer's name.",
              "any_of": [
                "Your friend",
                "Best wishes"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "arjun",
            "dear",
            "frogs",
            "visit",
            "have"
          ],
          "model_answer": "Hi Arjun, frogs sometimes visit the drain beside our sports field after rain. I once saw one resting under wet grass. What colour was the frog in your rain garden? Best wishes, Aman Reference evidence states: frogs visit.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:independent:3",
          "teaching_block": "Plan a direct answer, safe catch-up detail, and warm close; keep every factual claim tied to the supplied notes.",
          "passage": "Asha writes: 'I missed the pond walk because I was unwell. What did the guide show, and is there a safe way for me to catch up?' Notes: egg clusters under leaves; visitors stayed on marked paths; class photo sheet available.",
          "prompt": "Write a 35 to 55 word friendly reply that answers both questions and uses the notes accurately.",
          "skill_ids": [
            "writing.friendly_message",
            "writing.complete_sentence",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "answer",
              "description": "Explains what the guide showed.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safe_detail",
              "description": "Suggests the photo sheet instead of approaching eggs.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "friendly",
              "description": "Includes a caring close or useful question.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "answer",
              "description": "Explains what the guide showed.",
              "any_of": [
                "guide showed us egg clusters under leaves"
              ]
            },
            {
              "id": "safe_detail",
              "description": "Suggests the photo sheet instead of approaching eggs.",
              "any_of": [
                "using the class photo sheet"
              ]
            },
            {
              "id": "friendly",
              "description": "Includes a caring close or useful question.",
              "any_of": [
                "hope you feel better soon"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "asha",
            "writes",
            "missed",
            "pond",
            "walk",
            "because",
            "unwell",
            "what"
          ],
          "model_answer": "Hi Asha, the guide showed us egg clusters under leaves while everyone stayed on the marked paths. You can catch up safely by using the class photo sheet instead of approaching the eggs. I hope you feel better soon. Would you like me to share my notes too?",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "answer",
            "safe_detail",
            "friendly"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:independent:4",
          "teaching_block": "Answer the unsafe proposal immediately, give the supplied escalation path, and close with calm supportive language.",
          "passage": "Dev writes: 'I found a small frog near the classroom door. Should I pick it up and put it in my bag until lunch?' Safety card: do not handle; keep the area clear; tell an adult; adult contacts the campus nature volunteer.",
          "prompt": "Write a 35 to 55 word reply that is kind, direct, and safety-complete.",
          "skill_ids": [
            "writing.friendly_message",
            "writing.complete_sentence",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "boundary",
              "description": "Directly says not to handle or bag the frog.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Tells Dev to clear the area and inform an adult.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "tone",
              "description": "Closes supportively without praising unsafe action.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "boundary",
              "description": "Directly says not to handle or bag the frog.",
              "any_of": [
                "do not pick up the frog"
              ]
            },
            {
              "id": "action",
              "description": "Tells Dev to clear the area and inform an adult.",
              "any_of": [
                "keep the doorway clear and tell an adult"
              ]
            },
            {
              "id": "tone",
              "description": "Closes supportively without praising unsafe action.",
              "any_of": [
                "right thing by asking before acting"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "writes",
            "found",
            "small",
            "frog",
            "near",
            "classroom",
            "door",
            "should"
          ],
          "model_answer": "Hi Dev, please do not pick up the frog or put it in your bag. Keep the doorway clear and tell an adult straight away. The adult can contact the campus nature volunteer for help. You did the right thing by asking before acting.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "boundary",
            "action",
            "tone"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:transfer:1",
          "teaching_block": "Write a complete message with greeting, direct response, relevant detail, connected question, closing, and name. Explain the first part before connecting it to the result.",
          "passage": "Dear friend, I heard loud croaks near my window last night. Have you heard them near your home? - Nisha",
          "prompt": "Reply in 35 to 55 words with an answer, detail, question, and closing.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "answer",
              "description": "Answers Nisha's question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "detail",
              "description": "Adds a relevant time/place/call detail.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "question",
              "description": "Asks one related question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "closing",
              "description": "Includes greeting, closing, and name.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "answer",
              "description": "Answers Nisha's question.",
              "any_of": [
                "I have heard",
                "I have not heard"
              ]
            },
            {
              "id": "detail",
              "description": "Adds a relevant time/place/call detail.",
              "any_of": [
                "after rain",
                "near the lane",
                "deep croaks"
              ]
            },
            {
              "id": "question",
              "description": "Asks one related question.",
              "any_of": [
                "how long",
                "where were they",
                "was it raining"
              ]
            },
            {
              "id": "closing",
              "description": "Includes greeting, closing, and name.",
              "any_of": [
                "Hi Nisha",
                "Your friend"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "have",
            "heard",
            "after",
            "rain",
            "near"
          ],
          "model_answer": "Hi Nisha, I have heard frog calls near the small drain behind our home after rain. The croaks continued for several minutes. Was it raining when you heard them near your window? Your friend, Meera",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:transfer:2",
          "teaching_block": "Write a complete message with greeting, direct response, relevant detail, connected question, closing, and name. Use your own words while preserving every required idea.",
          "passage": "Hi! Our class visited a wetland, and I saw a frog vanish among green plants. Have you seen anything similar? - Maya",
          "prompt": "Write a 35 to 55 word reply that stays on Maya's topic.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "answer",
              "description": "Answers the similar-observation question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "detail",
              "description": "Adds a relevant hiding or wetland detail.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "question",
              "description": "Asks Maya one connected question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "structure",
              "description": "Uses greeting, closing, and name.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "answer",
              "description": "Answers the similar-observation question.",
              "any_of": [
                "I saw",
                "I have not seen"
              ]
            },
            {
              "id": "detail",
              "description": "Adds a relevant hiding or wetland detail.",
              "any_of": [
                "among leaves",
                "near water",
                "blended with plants"
              ]
            },
            {
              "id": "question",
              "description": "Asks Maya one connected question.",
              "any_of": [
                "how long",
                "what colour",
                "where in the wetland"
              ]
            },
            {
              "id": "structure",
              "description": "Uses greeting, closing, and name.",
              "any_of": [
                "Hi Maya",
                "Best wishes"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "have",
            "seen",
            "among",
            "leaves",
            "near"
          ],
          "model_answer": "Hi Maya, I once saw a brown frog remain still among wet leaves beside a pond. I nearly missed it because its colour matched the ground. What colour was the frog at your wetland? Best wishes, Kabir Reference evidence states: I saw; among leaves.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:transfer:3",
          "teaching_block": "Transfer the reply structure to an information request: answer, source, and friendly next step.",
          "passage": "Mina writes: 'The library display says insects help ponds. I do not understand how. Can you explain one example and suggest where I can read more?' Source note: dragonfly nymphs eat some mosquito larvae; illustrated wetland guide is on shelf 4.",
          "prompt": "Write a 35 to 55 word friendly reply using both source-note details and one inviting close.",
          "skill_ids": [
            "writing.friendly_message",
            "writing.complete_sentence",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "example",
              "description": "Explains the dragonfly-nymph example accurately.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "resource",
              "description": "Directs Mina to the shelf-4 wetland guide.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "close",
              "description": "Ends with a friendly invitation.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "example",
              "description": "Explains the dragonfly-nymph example accurately.",
              "any_of": [
                "dragonfly nymphs eat some mosquito larvae"
              ]
            },
            {
              "id": "resource",
              "description": "Directs Mina to the shelf-4 wetland guide.",
              "any_of": [
                "wetland guide on shelf 4"
              ]
            },
            {
              "id": "close",
              "description": "Ends with a friendly invitation.",
              "any_of": [
                "look at it together after class"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "mina",
            "writes",
            "'the",
            "library",
            "display",
            "says",
            "insects",
            "help"
          ],
          "model_answer": "Hi Mina, one example is that dragonfly nymphs eat some mosquito larvae in pond water. The illustrated wetland guide on shelf 4 explains more pond relationships. We could look at it together after class if you would like.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "example",
            "resource",
            "close"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:transfer:4",
          "teaching_block": "Answer the sender's actual question, add relevant packet information, ask one connected question, and close politely. Apply the same construct to this new passage. Use the visible passage to practise sentence comprehension and friendly message and complete sentence; include both details.",
          "passage": "Hi! I found frog eggs in a shallow tyre track beside our playing field. The nature-club card says not to touch them and to tell an adult so the area can be marked. What should I do first? - Iqra",
          "prompt": "Reply to Iqra in 35 to 55 words with the first action, the no-touch reason, one related question, and a polite close.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "frog_friendly_reply:transfer:4:answer",
              "description": "Answers with adult reporting and the no-touch reason.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_friendly_reply:transfer:4:message",
              "description": "Includes a related question and friendly close.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_friendly_reply:transfer:4:answer",
              "description": "Answers with adult reporting and the no-touch reason.",
              "any_of": [
                "tell a teacher or another adult first",
                "Do not touch the eggs",
                "damage their wet habitat"
              ]
            },
            {
              "id": "frog_friendly_reply:transfer:4:message",
              "description": "Includes a related question and friendly close.",
              "any_of": [
                "Is the track close",
                "Take care, Riya"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "teacher",
            "another",
            "adult"
          ],
          "model_answer": "Hi Iqra, tell a teacher or another adult first so the tyre track can be marked and protected. Do not touch the eggs because moving them may damage their wet habitat. Is the track close to where vehicles pass? Take care, Riya",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:review:1",
          "teaching_block": "Write a complete message with greeting, direct response, relevant detail, connected question, closing, and name. Apply the same reasoning to a different setting and justify it.",
          "passage": "Hello! I found a tiny frog beside a puddle after the storm. What should I do when I see one? - Dev",
          "prompt": "Reply in 35 to 55 words with a cautious action and a related question.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "advice",
              "description": "Gives a cautious non-handling action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains that crowding or handling may disturb it.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "question",
              "description": "Asks a related question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "structure",
              "description": "Includes greeting, closing, and name.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "advice",
              "description": "Gives a cautious non-handling action.",
              "any_of": [
                "watch from a distance",
                "leave it space",
                "ask an adult"
              ]
            },
            {
              "id": "reason",
              "description": "Explains that crowding or handling may disturb it.",
              "any_of": [
                "do not disturb",
                "handling can hurt"
              ]
            },
            {
              "id": "question",
              "description": "Asks a related question.",
              "any_of": [
                "was it moving",
                "near a road",
                "what colour"
              ]
            },
            {
              "id": "structure",
              "description": "Includes greeting, closing, and name.",
              "any_of": [
                "Hi Dev",
                "Your friend"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "watch",
            "from",
            "distance",
            "leave",
            "space"
          ],
          "model_answer": "Hi Dev, I would watch the frog from a distance and give it space instead of picking it up. If it were near traffic, I would ask an adult for help. Was the puddle close to the road? Your friend, Sara Reference evidence states: do not disturb; was it moving.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:review:2",
          "teaching_block": "Write a complete message with greeting, direct response, relevant detail, connected question, closing, and name. Separate what is stated from what can reasonably be inferred.",
          "passage": "Dear reader, I like splashing in puddles and eating insects. What do you like to do? - Hopper",
          "prompt": "Write Hopper a 35 to 55 word reply that answers the personal question and remains friendly.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "greeting",
              "description": "Greets Hopper.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "answer",
              "description": "States one activity the writer likes.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "connection",
              "description": "Responds briefly to Hopper's puddle or insect detail.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "question",
              "description": "Asks Hopper one related question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "closing",
              "description": "Includes closing and name.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "greeting",
              "description": "Greets Hopper.",
              "any_of": [
                "Dear Hopper",
                "Hi Hopper"
              ]
            },
            {
              "id": "answer",
              "description": "States one activity the writer likes.",
              "any_of": [
                "I like to",
                "My favourite activity"
              ]
            },
            {
              "id": "connection",
              "description": "Responds briefly to Hopper's puddle or insect detail.",
              "any_of": [
                "puddles sound",
                "you like insects",
                "after rain"
              ]
            },
            {
              "id": "question",
              "description": "Asks Hopper one related question.",
              "any_of": [
                "which puddle",
                "when do you croak",
                "what insect"
              ]
            },
            {
              "id": "closing",
              "description": "Includes closing and name.",
              "any_of": [
                "Your friend",
                "Best wishes"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "dear",
            "hopper",
            "like",
            "favourite",
            "activity"
          ],
          "model_answer": "Dear Hopper, I like cycling slowly in the park after rain. Your puddle games sound lively, although I prefer staying dry. Which insects do you find near your lily pad? Your friend, Aarav Reference evidence states: I like to; which puddle.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:review:3",
          "teaching_block": "Answer the sender's actual question, add relevant packet information, ask one connected question, and close politely. Retrieve the construct, then verify it against the passage. Use the visible passage to practise sentence comprehension and friendly message and complete sentence; include both details.",
          "passage": "Dear friend, our pond survey found fewer tadpoles near the littered bank. The class plans a supervised clean-up but will not enter the water. What safe job could I choose? - Sameer",
          "prompt": "Write Sameer a 35 to 55 word reply with one safe job, one reason, a connected question, and a closing.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "frog_friendly_reply:review:3:response",
              "description": "Suggests dry-bank recording and explains its survey value.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_friendly_reply:review:3:form",
              "description": "Includes the adult-safety question and friendly closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_friendly_reply:review:3:response",
              "description": "Suggests dry-bank recording and explains its survey value.",
              "any_of": [
                "record each bag of litter",
                "compare future surveys"
              ]
            },
            {
              "id": "frog_friendly_reply:review:3:form",
              "description": "Includes the adult-safety question and friendly closing.",
              "any_of": [
                "Will an adult mark",
                "Your friend, Kabir"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "sameer",
            "record",
            "litter"
          ],
          "model_answer": "Dear Sameer, you could record each bag of litter collected from the dry bank because accurate notes will help the class compare future surveys. Will an adult mark the safe working area before you begin? I hope the clean-up goes well. Your friend, Kabir",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "frog_friendly_reply:review:4",
          "teaching_block": "Answer the sender's actual question, add relevant packet information, ask one connected question, and close politely. Retrieve the construct, then verify it against the passage. Use the visible passage to practise sentence comprehension and friendly message and complete sentence; include both details.",
          "passage": "Hello! I photographed a frog from the path without using flash. The field guide says its brown stripe may help identification, but I should record place and time too. What should my note include? - Tara",
          "prompt": "Reply in 35 to 55 words using all three record details, one encouraging sentence, a question, and a polite close.",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "interaction_type": "dialogue",
          "rubric_criteria": [
            {
              "id": "frog_friendly_reply:review:4:details",
              "description": "Includes stripe, place, and time from Tara's message.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_friendly_reply:review:4:reply",
              "description": "Responds encouragingly, asks a related question, and closes.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_friendly_reply:review:4:details",
              "description": "Includes stripe, place, and time from Tara's message.",
              "any_of": [
                "brown stripe",
                "exact place",
                "the time"
              ]
            },
            {
              "id": "frog_friendly_reply:review:4:reply",
              "description": "Responds encouragingly, asks a related question, and closes.",
              "any_of": [
                "was careful work",
                "Did you also notice",
                "Best wishes, Neel"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "hello",
            "brown",
            "stripe"
          ],
          "model_answer": "Hello Tara, note the brown stripe, the exact place, and the time beside your photograph. Staying on the path and avoiding flash was careful work. Did you also notice whether the frog was near water or dry leaves? Best wishes, Neel",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "reply-structure-or-topic-drift",
          "skill_ids": [
            "reading.sentence_comprehension",
            "writing.friendly_message",
            "writing.complete_sentence"
          ],
          "misconception": "The learner writes a generic paragraph, ignores the sender's actual question, or omits the greeting, related question, closing, or writer name.",
          "remediation": "Highlight the sender's question, draft answer-detail-question in three boxes, then add the greeting and signed closing around those boxes.",
          "support_check_ids": [
            "frog_friendly_reply:support:bridge",
            "frog_friendly_reply:support:masterclass",
            "frog_friendly_reply:support:revision_level_1",
            "frog_friendly_reply:support:revision_level_2",
            "frog_friendly_reply:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "frog_friendly_reply:support:bridge",
          "teaching_block": "Use the sender's question and details to identify the reply that stays relevant. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "A reply begins 'Dear Zoya,'.",
          "prompt": "Which closing is appropriate?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "Because the pond",
            "Your friend, Ria",
            "Frogs quickly",
            "Question mark"
          ],
          "accepted_answers": [
            "Your friend, Ria"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "frog_friendly_reply:support:masterclass",
          "teaching_block": "Use the sender's question and details to identify the reply that stays relevant. Reject any option that adds a fact the passage never gives.",
          "passage": "Arjun asks if you have seen small animals near school.",
          "prompt": "Which detail is relevant?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "I saw a snail beside the rain garden.",
            "Our classroom wall is white.",
            "I packed two notebooks.",
            "Lunch starts at noon."
          ],
          "accepted_answers": [
            "I saw a snail beside the rain garden."
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "frog_friendly_reply:support:revision_level_1",
          "teaching_block": "Use the sender's question and details to identify the reply that stays relevant. Break the task into one smaller decision and check it carefully.",
          "passage": "The sender says frogs called beside the sports field after a shower.",
          "prompt": "Which response shows careful reading?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "I also heard calls after rain near our field.",
            "Fish have fins.",
            "I prefer drawing stars.",
            "The message has many words."
          ],
          "accepted_answers": [
            "I also heard calls after rain near our field."
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "frog_friendly_reply:support:revision_level_2",
          "teaching_block": "Use the sender's question and details to identify the reply that stays relevant. Name the rule first, then apply it to this new example.",
          "passage": "A friendly reply needs a direct answer and one related question.",
          "prompt": "Which pair fulfils both roles?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "Yes, frogs visit our lane. Where did you see yours?",
            "Frogs are animals. Goodbye.",
            "Maybe. My bag is red.",
            "Hello. Rain exists."
          ],
          "accepted_answers": [
            "Yes, frogs visit our lane. Where did you see yours?"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "frog_friendly_reply:support:revision_level_3",
          "teaching_block": "Use the sender's question and details to identify the reply that stays relevant. Compare the tempting error with the evidence that corrects it.",
          "passage": "The sender's name is Hopper.",
          "prompt": "Which greeting is correctly addressed?",
          "skill_ids": [
            "reading.sentence_comprehension"
          ],
          "options": [
            "Dear Reader,",
            "Dear Hopper,",
            "Your Hopper,",
            "Goodbye Hopper,"
          ],
          "accepted_answers": [
            "Dear Hopper,"
          ]
        }
      }
    },
    {
      "level_id": "frog_instruction_and_research",
      "title": "Follow and explain an aquatic mission",
      "focus": "sequence supplied instructions and select bounded facts",
      "outcome": "Turn supplied observation or making instructions into an ordered procedure and report relevant aquatic-animal facts while keeping drawing, speaking, and listening as activities that need direct observation.",
      "skill_ids": [
        "writing.procedure",
        "research.information_selection"
      ],
      "episode_kind": "application_mission",
      "source_anchor_ids": [
        "eng_c5_ch05:explore:10"
      ],
      "companion_source_anchor_ids": [
        "eng_c5_ch05:do:8-9"
      ],
      "connect": {
        "teaching_block": "Written instruction cards help you practise sequencing and selecting facts. Keep each step in order and use only details shown in the card.",
        "passage": "Instruction card: first choose a damp setting, then place the frog, label two habitat features, and finally add colour.",
        "prompt": "Continue when you can retell the four instructions in order."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "frog_instruction_and_research:co_construct",
        "teaching_block": "Read the whole card, then choose the next step or the exact fact that answers the question.",
        "passage": "Steps: choose a setting; draw the frog; label habitat words; add colour.",
        "prompt": "Which step comes directly after choosing the setting?",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "add colour",
          "draw the frog",
          "label the final date",
          "research a dolphin"
        ],
        "accepted_answers": [
          "draw the frog"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "frog_instruction_and_research:guided:1",
          "teaching_block": "Read the whole question and packet, then test which fact answers exactly what was asked.",
          "passage": "Question: Which animal uses sound to navigate? Packet: The Ganges river dolphin has poor eyesight and uses sound to find its way.",
          "prompt": "Which fact answers the question?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "it is a river dolphin",
            "it uses sound to find its way",
            "it lives near every pond",
            "it draws maps"
          ],
          "accepted_answers": [
            "it uses sound to find its way"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:guided:2",
          "teaching_block": "Turn each written step into a complete sentence, keep the steps in order, and check that none is missing.",
          "passage": "Steps: choose the setting; add the frog; label water and shelter; write one sentence.",
          "prompt": "Write the four instructions in order as complete sentences.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "setting_frog",
              "description": "Orders setting before adding the frog.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "labels_sentence",
              "description": "Orders labels before the final sentence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "setting_frog",
              "description": "Orders setting before adding the frog.",
              "any_of": [
                "first choose the setting",
                "then add the frog"
              ]
            },
            {
              "id": "labels_sentence",
              "description": "Orders labels before the final sentence.",
              "any_of": [
                "label water and shelter",
                "then write one sentence"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "first",
            "choose",
            "setting",
            "then",
            "frog"
          ],
          "model_answer": "First choose the setting and then add the frog. Next, label the water and shelter, and finally write one sentence. Reference evidence states: label water and shelter.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "setting_frog",
            "labels_sentence"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_instruction_and_research:guided:3",
          "teaching_block": "Choose every required observation step and include every safety rule from the card.",
          "passage": "Observation card: use a notebook; remain on the marked path; listen for one minute; record time and number of calls; do not play recordings.",
          "prompt": "Which procedure follows every boundary?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "Leave the path and play loud calls to attract frogs.",
            "Record a count before listening and omit the time.",
            "Stay on the path, listen silently for one minute, and record the time and call count without playing recordings.",
            "Handle a frog so the notebook entry is exact."
          ],
          "accepted_answers": [
            "Stay on the path, listen silently for one minute, and record the time and call count without playing recordings."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "frog_instruction_and_research:guided:4",
          "teaching_block": "If two sources disagree, name both claims and ask which source is current instead of inventing an answer.",
          "passage": "Two sources disagree about a frog's maximum size. The task card says to record both claims and ask a teacher which source is current.",
          "prompt": "What is the correct next step?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "Choose the larger number because it sounds impressive.",
            "Combine both numbers into a new unsourced average.",
            "Delete the disagreement and report certainty.",
            "Record both attributed claims and ask which source is current."
          ],
          "accepted_answers": [
            "Record both attributed claims and ask which source is current."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:independent:1",
          "teaching_block": "Put every written step in order and use the card to explain which work happens on paper.",
          "passage": "Instruction card: choose a pond or rainy setting; add a frog; label two habitat features; write one sentence; colour last.",
          "prompt": "Write the five steps in order and identify the drawing and colouring steps.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "order",
              "description": "Orders setting, frog, labels, sentence, then colour.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "sentence_step",
              "description": "Includes the sentence-writing step before colouring.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "order",
              "description": "Orders setting, frog, labels, sentence, then colour.",
              "any_of": [
                "first choose",
                "then add",
                "colour last"
              ]
            },
            {
              "id": "sentence_step",
              "description": "Includes the sentence-writing step before colouring.",
              "any_of": [
                "write one sentence",
                "sentence before colour",
                "then write"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "first",
            "choose",
            "then",
            "colour",
            "last"
          ],
          "model_answer": "First choose a damp setting, then draw the frog. Label two habitat features and write one sentence about them before adding colour last.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "order",
            "sentence_step"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:independent:2",
          "teaching_block": "Choose the facts that answer the question and report each one in a complete sentence.",
          "passage": "Packet: Puffer fish—can inflate its body; seahorse—upright swimmer with curled tail; octopus—eight arms and soft body.",
          "prompt": "Select two animals and report one supplied fact for each.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "animal_one",
              "description": "Reports one accurate supplied puffer/seahorse/octopus fact.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "animal_two",
              "description": "Reports a different animal's supplied fact.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "animal_one",
              "description": "Reports one accurate supplied puffer/seahorse/octopus fact.",
              "any_of": [
                "puffer fish can inflate",
                "seahorse has a curled tail",
                "octopus has eight arms"
              ]
            },
            {
              "id": "animal_two",
              "description": "Reports a different animal's supplied fact.",
              "any_of": [
                "seahorse swims upright",
                "octopus has a soft body",
                "puffer fish inflates"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 16,
          "relevance_terms": [
            "puffer",
            "fish",
            "inflate",
            "seahorse",
            "curled"
          ],
          "model_answer": "The seahorse swims upright and has a curled tail. The octopus has eight arms and a soft body.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:independent:3",
          "teaching_block": "Turn the study card into an ordered plan. Name the source, write facts in your own words, record a question, and keep the safety rule.",
          "passage": "Offline study card: choose one library field guide; note title and page; copy no full sentences; record two facts in your own words; mark one unanswered question; ask an adult before visiting any site.",
          "prompt": "Write the ordered study procedure with every research and safety condition.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "source",
              "description": "Selects one guide and records title and page.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "paraphrase",
              "description": "Records two facts without copying full sentences.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "question",
              "description": "Marks one unanswered question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safety",
              "description": "Requires adult approval before a site visit.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "source",
              "description": "Selects one guide and records title and page.",
              "any_of": [
                "record its title and page"
              ]
            },
            {
              "id": "paraphrase",
              "description": "Records two facts without copying full sentences.",
              "any_of": [
                "paraphrase two facts"
              ]
            },
            {
              "id": "question",
              "description": "Marks one unanswered question.",
              "any_of": [
                "mark one unanswered question"
              ]
            },
            {
              "id": "safety",
              "description": "Requires adult approval before a site visit.",
              "any_of": [
                "ask an adult before planning any site visit"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 28,
          "relevance_terms": [
            "offline",
            "study",
            "card",
            "choose",
            "library",
            "field",
            "guide",
            "note"
          ],
          "model_answer": "Choose one library field guide and record its title and page. Paraphrase two facts rather than copying full sentences, then mark one unanswered question. Ask an adult before planning any site visit.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "source",
            "paraphrase",
            "question",
            "safety"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:independent:4",
          "teaching_block": "Separate what the data shows from what it cannot explain, then make the missing variable a concrete next-step instruction.",
          "passage": "Data card: Site A, 8 calls in one minute at 6:10 p.m.; Site B, 3 calls in one minute at 6:20 p.m. Both observations used the same method. Weather was not recorded.",
          "prompt": "Compare what the numbers show without guessing why, then name one fact to record next time.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "comparison",
              "description": "Reports the eight-versus-three observation accurately.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "States that missing weather blocks explanation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "Instructs the observer to record weather next time.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "comparison",
              "description": "Reports the eight-versus-three observation accurately.",
              "any_of": [
                "site A had eight recorded calls"
              ]
            },
            {
              "id": "limit",
              "description": "States that missing weather blocks explanation.",
              "any_of": [
                "weather was not noted"
              ]
            },
            {
              "id": "next",
              "description": "Instructs the observer to record weather next time.",
              "any_of": [
                "record weather alongside time"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 28,
          "relevance_terms": [
            "data",
            "card",
            "site",
            "calls",
            "minute",
            "both",
            "observations",
            "used"
          ],
          "model_answer": "Using the same one-minute method, Site A had eight recorded calls while Site B had three. The record cannot explain the difference because weather was not noted. Next time, record weather alongside time and call count.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "comparison",
            "limit",
            "next"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:transfer:1",
          "teaching_block": "Put the comparison steps in order and explain what each step checks.",
          "passage": "Procedure notes: examine the first image; examine the second; list only visible differences; verify each difference once more.",
          "prompt": "Turn the notes into a reliable comparison procedure.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "examine",
              "description": "Orders examining both images before listing differences.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "visible",
              "description": "Limits the list to visible differences.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "verify",
              "description": "Ends with checking each reported difference.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "examine",
              "description": "Orders examining both images before listing differences.",
              "any_of": [
                "examine both images",
                "look at first and second"
              ]
            },
            {
              "id": "visible",
              "description": "Limits the list to visible differences.",
              "any_of": [
                "only visible differences",
                "do not guess"
              ]
            },
            {
              "id": "verify",
              "description": "Ends with checking each reported difference.",
              "any_of": [
                "verify each difference",
                "check again"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "examine",
            "both",
            "images",
            "look",
            "first"
          ],
          "model_answer": "First examine both images carefully. Next, list only differences that are visible rather than guessed. Finally, check each reported difference against both images once more. Reference evidence states: only visible differences; verify each difference.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "examine",
            "visible",
            "verify"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:transfer:2",
          "teaching_block": "Use your own words while preserving each animal and its supplied feature.",
          "passage": "Packet: River dolphin—uses sound to navigate; jellyfish—moves with water currents and has tentacles; catfish—has barbels near its mouth.",
          "prompt": "Answer: Which feature belongs to each animal? Report all three without extra claims.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "dolphin",
              "description": "Reports sound navigation for the river dolphin.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "jellyfish",
              "description": "Reports tentacles or movement with currents.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "catfish",
              "description": "Reports barbels near the mouth.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "dolphin",
              "description": "Reports sound navigation for the river dolphin.",
              "any_of": [
                "dolphin uses sound",
                "sound to navigate"
              ]
            },
            {
              "id": "jellyfish",
              "description": "Reports tentacles or movement with currents.",
              "any_of": [
                "jellyfish has tentacles",
                "moves with currents"
              ]
            },
            {
              "id": "catfish",
              "description": "Reports barbels near the mouth.",
              "any_of": [
                "catfish has barbels",
                "barbels near its mouth"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "dolphin",
            "uses",
            "sound",
            "navigate",
            "jellyfish"
          ],
          "model_answer": "The river dolphin uses sound to navigate, the jellyfish has tentacles and moves with currents, and the catfish has barbels near its mouth.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:transfer:3",
          "teaching_block": "Use the same research steps in this bird-count task. Include how long to watch, what to record, the safety rule, and how to submit.",
          "passage": "Bird-count card: stand at one fixed point; observe for five minutes; tally only birds seen or heard; note start time and weather; do not use food or recorded calls; submit the tally with location code.",
          "prompt": "Transfer the field-research procedure to this bird count in a safe ordered paragraph.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "setup",
              "description": "Uses fixed point, location code, time, and weather.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "observe",
              "description": "Observes five minutes and tallies seen or heard birds.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "Forbids food and recorded calls.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "submit",
              "description": "Submits tally with location code.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "setup",
              "description": "Uses fixed point, location code, time, and weather.",
              "any_of": [
                "fixed point and note the location code"
              ]
            },
            {
              "id": "observe",
              "description": "Observes five minutes and tallies seen or heard birds.",
              "any_of": [
                "observe for five minutes"
              ]
            },
            {
              "id": "boundary",
              "description": "Forbids food and recorded calls.",
              "any_of": [
                "do not use food or recorded calls"
              ]
            },
            {
              "id": "submit",
              "description": "Submits tally with location code.",
              "any_of": [
                "submit the completed tally"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 30,
          "relevance_terms": [
            "bird",
            "count",
            "card",
            "stand",
            "fixed",
            "point",
            "observe",
            "five"
          ],
          "model_answer": "Stand at the fixed point and note the location code, start time, and weather. Observe for five minutes and tally only birds seen or heard. Do not use food or recorded calls. Submit the completed tally with the location code.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "setup",
            "observe",
            "boundary",
            "submit"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:transfer:4",
          "teaching_block": "Select the bounded facts, place actions in a safe workable order, and state what the procedure records. Apply the same construct to this new passage. Use the visible passage to practise procedure and information selection; include both details.",
          "passage": "Water-observation card: label three clear jars A, B, and C; an adult fills them from three marked points; place jars on a white tray; compare colour without tasting or touching; record only visible differences; seal and return jars to the adult.",
          "prompt": "Write the safe ordered procedure and state exactly what evidence may be recorded.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "frog_instruction_and_research:transfer:4:steps",
              "description": "Orders labelling, adult filling, tray comparison, and recording.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_instruction_and_research:transfer:4:safety",
              "description": "Preserves no tasting or touching and the final adult return.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_instruction_and_research:transfer:4:steps",
              "description": "Orders labelling, adult filling, tray comparison, and recording.",
              "any_of": [
                "First label the clear jars",
                "adult fill them",
                "white tray",
                "Record only visible differences"
              ]
            },
            {
              "id": "frog_instruction_and_research:transfer:4:safety",
              "description": "Preserves no tasting or touching and the final adult return.",
              "any_of": [
                "without tasting or touching",
                "return them to the adult"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "first",
            "label",
            "clear"
          ],
          "model_answer": "First label the clear jars A, B, and C, then let an adult fill them at the marked points. Place the jars on a white tray and compare their colour without tasting or touching the water. Record only visible differences. Finally, seal the jars and return them to the adult.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_instruction_and_research:transfer:4:steps",
            "frog_instruction_and_research:transfer:4:safety"
          ]
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:review:1",
          "teaching_block": "Use the instruction card to retell every step in order, then explain which check keeps the work accurate.",
          "passage": "Garden poster card: choose a plant; sketch its stem and leaves; label two parts; check both labels; add colour after checking.",
          "prompt": "Write the five instructions in order and explain why checking comes before colouring.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "order",
              "description": "Orders all five poster-making steps.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "check",
              "description": "Explains that checking both labels before colouring prevents an unnoticed label error.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "order",
              "description": "Orders all five poster-making steps.",
              "any_of": [
                "first choose",
                "then sketch",
                "label",
                "check",
                "colour"
              ]
            },
            {
              "id": "check",
              "description": "Explains that checking both labels before colouring prevents an unnoticed label error.",
              "any_of": [
                "check the labels",
                "check both labels",
                "correct a label",
                "find a label mistake"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "plant",
            "sketch",
            "label",
            "check",
            "colour"
          ],
          "model_answer": "First choose a plant, then sketch its stem and leaves and label two parts. Check both labels before adding colour so a label mistake can be corrected first.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:review:2",
          "teaching_block": "Order every step and notice the check that keeps the work accurate.",
          "passage": "Duck-making card: sketch body; add head; place bill; add feet; check proportions; colour after checking.",
          "prompt": "Write the ordered procedure and identify the check-before-colour safeguard.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "steps",
              "description": "Orders body, head, bill, and feet.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "check",
              "description": "Places proportion checking before colouring.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "steps",
              "description": "Orders body, head, bill, and feet.",
              "any_of": [
                "body then head",
                "add bill",
                "add feet"
              ]
            },
            {
              "id": "check",
              "description": "Places proportion checking before colouring.",
              "any_of": [
                "check proportions before colour",
                "verify before colouring"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "body",
            "then",
            "head",
            "bill",
            "feet"
          ],
          "model_answer": "Sketch the body first, add the head, place the bill, and then add the feet. Check the proportions before adding colour. Reference evidence states: body then head; check proportions before colour.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "steps",
            "check"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:review:3",
          "teaching_block": "Select the bounded facts, place actions in a safe workable order, and state what the procedure records. Retrieve the construct, then verify it against the passage. Use the visible passage to practise procedure and information selection; include both details.",
          "passage": "Shadow-study card: mark one fixed stick; at 9 a.m., noon, and 3 p.m., trace the shadow tip on paper; label each time; measure each traced line; keep the stick unmoved; compare only the recorded lengths and directions.",
          "prompt": "Turn the card into an ordered observation procedure with its fixed-variable rule and evidence limit.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "frog_instruction_and_research:review:3:procedure",
              "description": "Orders the fixed stick, timed traces, labels, and measurements.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_instruction_and_research:review:3:limit",
              "description": "Restricts comparison to recorded lengths and directions.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_instruction_and_research:review:3:procedure",
              "description": "Orders the fixed stick, timed traces, labels, and measurements.",
              "any_of": [
                "keep it unmoved",
                "At 9 a.m., noon, and 3 p.m.",
                "label each time",
                "Measure every traced line"
              ]
            },
            {
              "id": "frog_instruction_and_research:review:3:limit",
              "description": "Restricts comparison to recorded lengths and directions.",
              "any_of": [
                "Compare only the recorded shadow lengths and directions",
                "unobserved times"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "fixed",
            "stick",
            "unmoved"
          ],
          "model_answer": "Mark one fixed stick and keep it unmoved. At 9 a.m., noon, and 3 p.m., trace the shadow tip on paper and label each time. Measure every traced line. Compare only the recorded shadow lengths and directions rather than guessing about unobserved times.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_instruction_and_research:review:3:procedure",
            "frog_instruction_and_research:review:3:limit"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "frog_instruction_and_research:review:4",
          "teaching_block": "Select the bounded facts, place actions in a safe workable order, and state what the procedure records. Retrieve the construct, then verify it against the passage. Use the visible passage to practise procedure and information selection; include both details.",
          "passage": "Library-research card: choose one aquatic animal; read two labelled fact cards; copy each card title; list one matching fact from each; circle any disagreement; ask the librarian before using another source; write a two-sentence report with both card titles.",
          "prompt": "Write the complete research procedure and explain how the final report stays traceable.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "frog_instruction_and_research:review:4:research",
              "description": "Orders card selection, title capture, fact matching, and disagreement marking.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "frog_instruction_and_research:review:4:trace",
              "description": "Includes librarian approval and title-based traceability.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "frog_instruction_and_research:review:4:research",
              "description": "Orders card selection, title capture, fact matching, and disagreement marking.",
              "any_of": [
                "read two labelled fact cards",
                "Copy both card titles",
                "one matching fact",
                "circle any disagreement"
              ]
            },
            {
              "id": "frog_instruction_and_research:review:4:trace",
              "description": "Includes librarian approval and title-based traceability.",
              "any_of": [
                "Ask the librarian",
                "names both card titles",
                "fact can be traced"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "choose",
            "aquatic",
            "animal"
          ],
          "model_answer": "Choose one aquatic animal and read two labelled fact cards. Copy both card titles, list one matching fact from each, and circle any disagreement. Ask the librarian before adding another source. Finish with a two-sentence report that names both card titles, so every included fact can be traced.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "frog_instruction_and_research:review:4:research",
            "frog_instruction_and_research:review:4:trace"
          ]
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "modality-overclaim-or-unordered-procedure",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "misconception": "The learner treats typed recall as proof of pronunciation, listening, or drawing performance, or lists procedure steps without a reliable order.",
          "remediation": "Separate browser-certifiable text evidence from teacher-observed performance, then number every supplied step and verify no action was invented.",
          "support_check_ids": [
            "frog_instruction_and_research:support:bridge",
            "frog_instruction_and_research:support:masterclass",
            "frog_instruction_and_research:support:revision_level_1",
            "frog_instruction_and_research:support:revision_level_2",
            "frog_instruction_and_research:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "frog_instruction_and_research:support:bridge",
          "teaching_block": "Use the relationship stated in the card instead of choosing a familiar-sounding word.",
          "passage": "Question: Which animal has a curled tail? Packet: Seahorse—upright swimmer with a curled tail; jellyfish—soft body with trailing tentacles.",
          "prompt": "Which supplied fact answers?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "jellyfish has tentacles",
            "seahorse has a curled tail",
            "both live on land",
            "seahorse has feathers"
          ],
          "accepted_answers": [
            "seahorse has a curled tail"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "frog_instruction_and_research:support:masterclass",
          "teaching_block": "Choose only the option supported by the card and reject any added fact.",
          "passage": "Procedure note: move only three counters; keep every other counter still; check the final direction.",
          "prompt": "Which rule must be followed?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "move every counter",
            "move exactly three counters",
            "remove the board",
            "change the goal"
          ],
          "accepted_answers": [
            "move exactly three counters"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "frog_instruction_and_research:support:revision_level_1",
          "teaching_block": "Break the task into one smaller decision and check it against the card.",
          "passage": "Packet: Octopus—eight arms and a soft body; catfish—whisker-like barbels near the mouth.",
          "prompt": "Which fact belongs to the catfish?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "eight arms",
            "soft body",
            "whisker-like barbels",
            "curled tail"
          ],
          "accepted_answers": [
            "whisker-like barbels"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "frog_instruction_and_research:support:revision_level_2",
          "teaching_block": "Name the rule first, then apply it to this new example.",
          "passage": "Observation steps: look carefully; note two visible details; compare with the second image; report only differences seen.",
          "prompt": "Which action comes before reporting?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "invent a missing colour",
            "compare with the second image",
            "close the book",
            "ask for the answer"
          ],
          "accepted_answers": [
            "compare with the second image"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "frog_instruction_and_research:support:revision_level_3",
          "teaching_block": "Compare the tempting error with the detail that corrects it.",
          "passage": "The companion asks a teacher to listen to pronunciation.",
          "prompt": "Which claim is supported by the written response alone?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "pronunciation has been observed",
            "the written word meanings are shown, while pronunciation still needs to be heard",
            "drawing accuracy has been observed",
            "listening skill has been observed"
          ],
          "accepted_answers": [
            "the written word meanings are shown, while pronunciation still needs to be heard"
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
        "activity_id": "eng_c5_ch05_assess_a01",
        "teaching_block": "Decide whether the line is an observation or imaginative exaggeration.",
        "passage": "A poem says the frog leaps until the clouds seem close.",
        "prompt": "How should the line be interpreted?",
        "skill_ids": [
          "reading.poetic_language"
        ],
        "options": [
          "a literal claim that frogs reach clouds",
          "an exaggerated image of a high jump",
          "a rule about cloud height",
          "proof that frogs fly"
        ],
        "accepted_answers": [
          "an exaggerated image of a high jump"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_a02",
        "teaching_block": "Retrieve the two settings stated in the observation.",
        "passage": "A frog rests beneath wet leaves, then dives into the pond when footsteps approach.",
        "prompt": "Which two settings does it use?",
        "skill_ids": [
          "reading.sentence_comprehension"
        ],
        "options": [
          "wet leaves and pond water",
          "a dry cave and a tree",
          "only the pond",
          "only the leaves"
        ],
        "accepted_answers": [
          "wet leaves and pond water"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_a03",
        "teaching_block": "Follow the complete change sequence and locate the stage between feeding and emergence.",
        "passage": "Chart: an egg rests on a leaf; a caterpillar hatches and feeds; a chrysalis forms; an adult butterfly emerges.",
        "prompt": "Which stage comes after the caterpillar feeds but before the adult emerges?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "the egg rests on a leaf",
          "a chrysalis forms",
          "the caterpillar hatches",
          "the adult butterfly emerges"
        ],
        "accepted_answers": [
          "a chrysalis forms"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_a04",
        "teaching_block": "Use the quick sideways movement clue.",
        "passage": "When a shadow crossed the rock, the tiny crab scuttled sideways into a narrow crack.",
        "prompt": "What does scuttled mean here?",
        "skill_ids": [
          "reading.word_meaning_context"
        ],
        "options": [
          "moved quickly with short steps",
          "slept beneath the rock",
          "made a loud warning call",
          "floated slowly on the water"
        ],
        "accepted_answers": [
          "moved quickly with short steps"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_a05",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Infer how the body pattern may help and support the inference with the setting.",
        "passage": "A mottled frog rests among mottled stones while a bird circles overhead.",
        "prompt": "Infer how the body pattern may help and support the inference with the setting.",
        "skill_ids": [
          "reading.inference_reason"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "inference",
            "description": "Infers that the matching pattern may make the frog harder to notice.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "evidence",
            "description": "Uses the match between the mottled frog and stones.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "inference",
            "description": "Infers that the matching pattern may make the frog harder to notice.",
            "any_of": [
              "harder to notice",
              "may be less visible"
            ]
          },
          {
            "id": "evidence",
            "description": "Uses the match between the mottled frog and stones.",
            "any_of": [
              "mottled frog matches the stones",
              "pattern resembles the setting"
            ]
          }
        ],
        "forbidden_phrases": [
          "completely invisible",
          "never visible"
        ],
        "min_response_words": 16,
        "relevance_terms": [
          "harder",
          "notice",
          "less",
          "visible",
          "mottled"
        ],
        "model_answer": "The mottled pattern may make the frog harder to notice because its appearance resembles the mottled stones around it. Reference evidence states: mottled frog matches the stones.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_a06",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Write a reason answer explaining how the feature helps.",
        "passage": "A frog has wide webbed back feet that push against pond water.",
        "prompt": "Write a reason answer explaining how the feature helps.",
        "skill_ids": [
          "writing.reason_answer"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "feature",
            "description": "Names the webbed back feet.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "function",
            "description": "Explains that they push water and support swimming.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "feature",
            "description": "Names the webbed back feet.",
            "any_of": [
              "webbed back feet",
              "wide webbed feet"
            ]
          },
          {
            "id": "function",
            "description": "Explains that they push water and support swimming.",
            "any_of": [
              "push water",
              "help it swim"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 13,
        "relevance_terms": [
          "webbed",
          "back",
          "feet",
          "wide",
          "push"
        ],
        "model_answer": "Webbed back feet help the frog swim because their broad surface pushes against the pond water. Reference evidence states: push water.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_a07",
        "teaching_block": "Select one shared movement feature and one supported difference from the two new animal cards.",
        "passage": "River otter: moves through water with webbed feet and surfaces often to breathe. Freshwater turtle: pushes through water with webbed feet and can remain submerged for longer periods.",
        "prompt": "Compare the otter and turtle with one accurate similarity and one difference.",
        "skill_ids": [
          "writing.compare_contrast"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "same",
            "description": "States that both use webbed feet to move through water.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "different",
            "description": "Contrasts frequent surfacing with longer submersion.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "same",
            "description": "States that both use webbed feet to move through water.",
            "any_of": [
              "both use webbed feet",
              "both move through water"
            ]
          },
          {
            "id": "different",
            "description": "Contrasts frequent surfacing with longer submersion.",
            "any_of": [
              "otter surfaces often",
              "turtle remains submerged longer"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 21,
        "relevance_terms": [
          "otter",
          "turtle",
          "webbed",
          "water",
          "submerged"
        ],
        "model_answer": "Both the river otter and freshwater turtle use webbed feet to move through water, but the otter surfaces often while the turtle can remain submerged longer. Reference evidence states: both use webbed feet; turtle remains submerged longer.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_a08",
        "teaching_block": "Identify the cause relationship before choosing.",
        "passage": "The frog pushes through pond water ___ its broad webbed feet move water backward.",
        "prompt": "Which connector completes the cause relationship?",
        "skill_ids": [
          "grammar.connectors_because_and_but"
        ],
        "options": [
          "or",
          "but",
          "because",
          "and"
        ],
        "accepted_answers": [
          "because"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_a09",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Write one complete reason sentence using every note.",
        "passage": "Notes: the frog; hides; under a leaf; because; the sun is hot.",
        "prompt": "Write one complete reason sentence using every note.",
        "skill_ids": [
          "writing.complete_sentence"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "action",
            "description": "States that the frog hides under a leaf.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "reason",
            "description": "Uses the hot sun after because.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "action",
            "description": "States that the frog hides under a leaf.",
            "any_of": [
              "frog hides under a leaf"
            ]
          },
          {
            "id": "reason",
            "description": "Uses the hot sun after because.",
            "any_of": [
              "because the sun is hot"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 10,
        "relevance_terms": [
          "frog",
          "hides",
          "under",
          "leaf",
          "because"
        ],
        "model_answer": "The frog hides under a leaf because the sun is hot.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_a10",
        "teaching_block": "Place the time clue, subject, action, manner, and location in a natural order.",
        "passage": "words: at dawn / a kingfisher / waited / quietly / on the branch",
        "prompt": "Which sentence is correctly ordered?",
        "skill_ids": [
          "grammar.sentence_order"
        ],
        "options": [
          "At dawn, a kingfisher waited quietly on the branch.",
          "A quietly kingfisher branch waited at dawn.",
          "Waited on dawn the kingfisher quietly branch.",
          "On the branch at waited a dawn kingfisher."
        ],
        "accepted_answers": [
          "At dawn, a kingfisher waited quietly on the branch."
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_a11",
        "teaching_block": "Choose an adverb that describes how the action happens.",
        "passage": "The heron stepped ___ through the shallow water.",
        "prompt": "Which manner adverb fits?",
        "skill_ids": [
          "grammar.adverbs"
        ],
        "options": [
          "tomorrow",
          "carefully",
          "weekly",
          "outside"
        ],
        "accepted_answers": [
          "carefully"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_a12",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Write Zoya a 35 to 55 word reply with greeting, answer, detail, question, closing, and name.",
        "passage": "Hi! I heard frogs beside the sports field after rain. Do you hear them near school? - Zoya",
        "prompt": "Write Zoya a 35 to 55 word reply with greeting, answer, detail, question, closing, and name.",
        "skill_ids": [
          "writing.friendly_message"
        ],
        "interaction_type": "dialogue",
        "rubric_criteria": [
          {
            "id": "greeting",
            "description": "Greets Zoya.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "answer",
            "description": "Answers the school question.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "detail",
            "description": "Adds a relevant call or rain detail.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "question",
            "description": "Asks one related question.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "closing",
            "description": "Includes a closing and name.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "greeting",
            "description": "Greets Zoya.",
            "any_of": [
              "Hi Zoya",
              "Dear Zoya"
            ]
          },
          {
            "id": "answer",
            "description": "Answers the school question.",
            "any_of": [
              "I hear frogs",
              "I have not heard frogs"
            ]
          },
          {
            "id": "detail",
            "description": "Adds a relevant call or rain detail.",
            "any_of": [
              "after rain",
              "near the drain",
              "loud croaks"
            ]
          },
          {
            "id": "question",
            "description": "Asks one related question.",
            "any_of": [
              "where did you hear",
              "was it raining"
            ]
          },
          {
            "id": "closing",
            "description": "Includes a closing and name.",
            "any_of": [
              "Your friend",
              "Best wishes"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 35,
        "relevance_terms": [
          "zoya",
          "dear",
          "hear",
          "frogs",
          "have"
        ],
        "model_answer": "Hi Zoya, I sometimes hear frogs near the drain behind our school after rain. Their deep croaks continue for several minutes. Was the sports field still wet when you heard them? Your friend, Riya Reference evidence states: I hear frogs; where did you hear.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_a13",
        "teaching_block": "Turn the safety card into an ordered procedure and explain the reading check.",
        "passage": "Rain-gauge card: ask an adult to cut the top from a clear bottle; turn the top upside down as a funnel; mark equal centimetre lines; place the bottle in an open area; read the water at eye level after rain; record the amount and empty the bottle.",
        "prompt": "Write the six steps in order and explain why the water is read at eye level.",
        "skill_ids": [
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "order",
            "description": "Orders all six supplied steps.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "check",
            "description": "Explains that reading at eye level makes the measurement more accurate.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "order",
            "description": "Orders all six supplied steps.",
            "any_of": [
              "first ask an adult",
              "turn the top upside down",
              "mark equal centimetre lines",
              "record the amount and empty"
            ]
          },
          {
            "id": "check",
            "description": "Explains that reading at eye level makes the measurement more accurate.",
            "any_of": [
              "read at eye level",
              "more accurate measurement",
              "avoid a reading error"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 25,
        "relevance_terms": [
          "adult",
          "bottle",
          "funnel",
          "centimetre",
          "level"
        ],
        "model_answer": "First ask an adult to cut the bottle top, then turn the top upside down as a funnel. Mark equal centimetre lines and place the bottle in an open area. After rain, read at eye level for a more accurate measurement. Record the amount and empty the bottle.",
        "pass_score": 0.8,
        "ordered_concept_slot_ids": [
          "order",
          "check"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_a14",
        "teaching_block": "Match the question's filter-feeding focus to the one fact that answers it directly.",
        "passage": "Question: Which animal filters tiny food from water? Packet: A flamingo strains water through its beak; a cormorant dives after fish.",
        "prompt": "Which packet fact directly answers the question?",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "the cormorant dives after fish",
          "the flamingo strains water through its beak",
          "both birds have feathers",
          "the packet compares two feeding methods"
        ],
        "accepted_answers": [
          "the flamingo strains water through its beak"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_a15",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Explain the mood and the words that create it.",
        "passage": "A verse calls the frog's croak a song and says it feels proud in its pond.",
        "prompt": "Explain the mood and the words that create it.",
        "skill_ids": [
          "reading.poetic_language"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "mood",
            "description": "Identifies a joyful, proud, or confident mood.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "evidence",
            "description": "Uses song or proud wording.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "mood",
            "description": "Identifies a joyful, proud, or confident mood.",
            "any_of": [
              "proud mood",
              "joyful",
              "confident"
            ]
          },
          {
            "id": "evidence",
            "description": "Uses song or proud wording.",
            "any_of": [
              "croak is called a song",
              "feels proud"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 13,
        "relevance_terms": [
          "proud",
          "mood",
          "joyful",
          "confident",
          "croak"
        ],
        "model_answer": "Calling the croak a song and describing pride in the pond creates a joyful, confident mood. Reference evidence states: croak is called a song.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_a16",
        "teaching_block": "Review the supplied procedure order.",
        "passage": "Instructions: inspect both images; list visible differences; verify each one.",
        "prompt": "Which step comes last?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "inspect the first image",
          "invent a difference",
          "verify each listed difference",
          "add a guessed difference"
        ],
        "accepted_answers": [
          "verify each listed difference"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b01",
        "teaching_block": "Separate the new poetic image from its impossible literal reading.",
        "passage": "At dusk, fireflies buttoned tiny stars onto the hedge.",
        "prompt": "What does the image suggest?",
        "skill_ids": [
          "reading.poetic_language"
        ],
        "options": [
          "the insects sew real buttons onto leaves",
          "their small lights appear like stars along the hedge",
          "stars fall from the sky into the garden",
          "the hedge is made from cloth"
        ],
        "accepted_answers": [
          "their small lights appear like stars along the hedge"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b02",
        "teaching_block": "Retrieve both actions stated in the sentence.",
        "passage": "A frog hops across moss and later floats beside the steps of a water tank.",
        "prompt": "Which statement matches the observation?",
        "skill_ids": [
          "reading.sentence_comprehension"
        ],
        "options": [
          "the frog uses a land surface and water",
          "the frog remains only on moss",
          "the frog never enters water",
          "the frog flies to the tank"
        ],
        "accepted_answers": [
          "the frog uses a land surface and water"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b03",
        "teaching_block": "Use transition words to locate the final stage.",
        "passage": "First eggs hatch, then back legs appear, later the front legs grow, and finally the tail shortens.",
        "prompt": "Which change is last?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "eggs hatch",
          "back legs appear",
          "front legs grow",
          "the tail shortens"
        ],
        "accepted_answers": [
          "the tail shortens"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b04",
        "teaching_block": "Use the shallow-water movement clue.",
        "passage": "The heron waded through ankle-deep water, lifting each long leg slowly above the mud.",
        "prompt": "What does waded mean here?",
        "skill_ids": [
          "reading.word_meaning_context"
        ],
        "options": [
          "walked through shallow water",
          "flew high above the river",
          "hid beneath dry leaves",
          "swam without touching the bottom"
        ],
        "accepted_answers": [
          "walked through shallow water"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_b05",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Infer how the two actions address danger differently, using both actions as evidence.",
        "passage": "A frog stays still against bark, then slips under a root when a shadow returns.",
        "prompt": "Infer how the two actions address danger differently, using both actions as evidence.",
        "skill_ids": [
          "reading.inference_reason"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "stillness",
            "description": "Explains that staying still can reduce noticeable movement.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "cover",
            "description": "Explains that moving under the root provides physical cover.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "stillness",
            "description": "Explains that staying still can reduce noticeable movement.",
            "any_of": [
              "stillness reduces notice",
              "staying still reduces movement"
            ]
          },
          {
            "id": "cover",
            "description": "Explains that moving under the root provides physical cover.",
            "any_of": [
              "root gives cover",
              "moves under shelter"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 17,
        "relevance_terms": [
          "stillness",
          "reduces",
          "notice",
          "staying",
          "still"
        ],
        "model_answer": "Staying still against the bark reduces noticeable movement, while slipping under the root provides physical cover when the shadow returns. Reference evidence states: stillness reduces notice; root gives cover.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_b06",
        "teaching_block": "Connect the feather coating to the supplied water condition and explain the practical advantage.",
        "passage": "A duck spread oil from a gland across its feathers before entering cold water. Drops rolled off instead of soaking through quickly.",
        "prompt": "Explain how the feather coating helps the duck in this scene.",
        "skill_ids": [
          "writing.reason_answer"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "effect",
            "description": "States that water rolls off instead of soaking through quickly.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "advantage",
            "description": "Explains that the coating helps the duck stay drier in cold water.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "effect",
            "description": "States that water rolls off instead of soaking through quickly.",
            "any_of": [
              "water rolls off",
              "does not soak through quickly"
            ]
          },
          {
            "id": "advantage",
            "description": "Explains that the coating helps the duck stay drier in cold water.",
            "any_of": [
              "keeps the duck drier",
              "helps in cold water"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 13,
        "relevance_terms": [
          "duck",
          "oil",
          "feathers",
          "water",
          "drier"
        ],
        "model_answer": "The oil coating makes water roll off the duck's feathers instead of soaking through quickly, which helps the duck stay drier in cold water. Reference evidence states: water rolls off; keeps the duck drier.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_b07",
        "teaching_block": "Compare how two birds use different beak structures to obtain food from water.",
        "passage": "Pelican: scoops fish near the surface with a broad pouch. Kingfisher: dives and grips one fish with a long pointed beak.",
        "prompt": "State one similarity and one supported difference in how the birds obtain fish.",
        "skill_ids": [
          "writing.compare_contrast"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "same",
            "description": "States that both birds use their beaks to obtain fish.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "different",
            "description": "Contrasts surface scooping with diving and gripping.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "same",
            "description": "States that both birds use their beaks to obtain fish.",
            "any_of": [
              "both use their beaks",
              "both obtain fish"
            ]
          },
          {
            "id": "different",
            "description": "Contrasts surface scooping with diving and gripping.",
            "any_of": [
              "pelican scoops",
              "kingfisher dives",
              "pointed beak grips"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 20,
        "relevance_terms": [
          "pelican",
          "kingfisher",
          "beak",
          "fish",
          "dives"
        ],
        "model_answer": "Both birds use their beaks to obtain fish, but the pelican scoops near the surface with a pouch while the kingfisher dives and grips one fish with a pointed beak. Reference evidence states: both use their beaks; kingfisher dives.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b08",
        "teaching_block": "Identify the contrast between the clauses.",
        "passage": "The pond looked quiet, ___ frog calls rose after sunset.",
        "prompt": "Which connector fits?",
        "skill_ids": [
          "grammar.connectors_because_and_but"
        ],
        "options": [
          "because",
          "or",
          "but",
          "and"
        ],
        "accepted_answers": [
          "but"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_b09",
        "teaching_block": "Join both possible waiting places in one complete alternative sentence.",
        "passage": "Notes: the kingfisher; may wait; on the fence post; or; on a low branch beside the stream.",
        "prompt": "Write one complete alternative sentence.",
        "skill_ids": [
          "writing.complete_sentence"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "post",
            "description": "Includes waiting on the fence post.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "branch",
            "description": "Uses or before the low-branch alternative.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "post",
            "description": "Includes waiting on the fence post.",
            "any_of": [
              "wait on the fence post"
            ]
          },
          {
            "id": "branch",
            "description": "Uses or before the low-branch alternative.",
            "any_of": [
              "or on a low branch beside the stream"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 11,
        "relevance_terms": [
          "kingfisher",
          "wait",
          "fence",
          "branch",
          "stream"
        ],
        "model_answer": "The kingfisher may wait on the fence post or on a low branch beside the stream.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b10",
        "teaching_block": "Place the subject before its action and keep the manner adverb near the verb.",
        "passage": "words: spider / a / carefully / weaves / its web",
        "prompt": "Which order is natural?",
        "skill_ids": [
          "grammar.sentence_order"
        ],
        "options": [
          "A carefully spider its web weaves.",
          "A spider carefully weaves its web.",
          "Weaves spider a carefully web.",
          "Its a web spider carefully."
        ],
        "accepted_answers": [
          "A spider carefully weaves its web."
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b11",
        "teaching_block": "Choose an adverb that answers how often.",
        "passage": "Frogs ___ call near the drain after summer rain.",
        "prompt": "Which frequency adverb fits?",
        "skill_ids": [
          "grammar.adverbs"
        ],
        "options": [
          "softly",
          "often",
          "nearby",
          "tomorrow"
        ],
        "accepted_answers": [
          "often"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_b12",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Write Arjun a 35 to 55 word reply with every message part.",
        "passage": "Hello! I found a frog beside our rain garden after the storm. Have you seen small animals near school? - Arjun",
        "prompt": "Write Arjun a 35 to 55 word reply with every message part.",
        "skill_ids": [
          "writing.friendly_message"
        ],
        "interaction_type": "dialogue",
        "rubric_criteria": [
          {
            "id": "greeting",
            "description": "Greets Arjun.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "answer",
            "description": "Answers whether small animals were seen.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "detail",
            "description": "Adds a relevant observation.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "question",
            "description": "Asks a connected question.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "closing",
            "description": "Includes closing and writer name.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "greeting",
            "description": "Greets Arjun.",
            "any_of": [
              "Hi Arjun",
              "Dear Arjun"
            ]
          },
          {
            "id": "answer",
            "description": "Answers whether small animals were seen.",
            "any_of": [
              "I saw",
              "I have not seen"
            ]
          },
          {
            "id": "detail",
            "description": "Adds a relevant observation.",
            "any_of": [
              "near the garden",
              "after rain",
              "snail",
              "frog"
            ]
          },
          {
            "id": "question",
            "description": "Asks a connected question.",
            "any_of": [
              "what colour",
              "where was it"
            ]
          },
          {
            "id": "closing",
            "description": "Includes closing and writer name.",
            "any_of": [
              "Your friend",
              "Best wishes"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 35,
        "relevance_terms": [
          "arjun",
          "dear",
          "have",
          "seen",
          "near"
        ],
        "model_answer": "Hi Arjun, I saw a small snail beside our school garden after rain last week. It moved slowly under a wet leaf. What colour was the frog in your rain garden? Best wishes, Kabir The response connects each required detail to the supplied evidence.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_b13",
        "teaching_block": "Turn the fresh germination card into an ordered procedure, keeping setup before sealing and observation after labelling.",
        "passage": "Bean card: fold a paper towel; dampen it; place one bean inside; slide it into a clear pouch; seal the pouch; label the date; observe daily.",
        "prompt": "Write the complete ordered bean-observation procedure and identify the final repeating action.",
        "skill_ids": [
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "steps",
            "description": "Orders folding, dampening, and placing the bean.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "finish",
            "description": "Places pouching and sealing before dating and daily observation.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "steps",
            "description": "Orders folding, dampening, and placing the bean.",
            "any_of": [
              "fold the paper towel",
              "dampen it",
              "place the bean"
            ]
          },
          {
            "id": "finish",
            "description": "Places pouching and sealing before dating and daily observation.",
            "any_of": [
              "seal the pouch",
              "label the date",
              "observe daily"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 20,
        "relevance_terms": [
          "paper",
          "towel",
          "bean",
          "pouch",
          "observe"
        ],
        "model_answer": "Fold and dampen the paper towel, then place one bean inside it. Slide the towel into a clear pouch and seal it. Label the date and observe the bean daily. Reference evidence states: fold the paper towel; observe daily.",
        "pass_score": 0.8,
        "ordered_concept_slot_ids": [
          "steps",
          "finish"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b14",
        "teaching_block": "Select only the fact tied to the named animal.",
        "passage": "Packet: Seahorse—upright swimmer with curled tail; jellyfish—tentacles; catfish—barbels.",
        "prompt": "Which fact belongs to the seahorse?",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "it has barbels",
          "it has tentacles",
          "it swims upright with a curled tail",
          "it has eight arms"
        ],
        "accepted_answers": [
          "it swims upright with a curled tail"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch05_assess_b15",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Explain the image using both details without claiming perfect invisibility.",
        "passage": "The poem says the frog's colours match leaves and that it hides well in grass.",
        "prompt": "Explain the image using both details without claiming perfect invisibility.",
        "skill_ids": [
          "reading.poetic_language"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "match",
            "description": "States that the colours match leaves or grass.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "effect",
            "description": "Explains that the match makes hiding easier or notice harder.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "match",
            "description": "States that the colours match leaves or grass.",
            "any_of": [
              "colours match leaves",
              "blends with grass"
            ]
          },
          {
            "id": "effect",
            "description": "Explains that the match makes hiding easier or notice harder.",
            "any_of": [
              "harder to notice",
              "helps it hide"
            ]
          }
        ],
        "forbidden_phrases": [
          "completely invisible",
          "never seen"
        ],
        "min_response_words": 15,
        "relevance_terms": [
          "colours",
          "match",
          "leaves",
          "blends",
          "with"
        ],
        "model_answer": "The frog's colours blend with the leaves and grass, which helps it hide and may make it harder to notice. Reference evidence states: colours match leaves.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch05_assess_b16",
        "teaching_block": "Use the complete making sequence to identify the immediately preceding action.",
        "passage": "Steps: place a leaf under paper; hold the paper still; rub with the side of a crayon; label the leaf veins; compare the finished pattern.",
        "prompt": "Which action happens immediately before comparing the finished pattern?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "place the leaf under the paper",
          "hold the paper still",
          "rub with the side of a crayon",
          "label the leaf veins"
        ],
        "accepted_answers": [
          "label the leaf veins"
        ]
      }
    ],
    "strands": [
      {
        "strand_id": "integrated-frog-performance",
        "skill_ids": [
          "grammar.adverbs",
          "grammar.connectors_because_and_but",
          "grammar.sentence_order",
          "reading.event_sequence",
          "reading.inference_reason",
          "reading.poetic_language",
          "reading.sentence_comprehension",
          "reading.word_meaning_context",
          "research.information_selection",
          "writing.compare_contrast",
          "writing.complete_sentence",
          "writing.friendly_message",
          "writing.procedure",
          "writing.reason_answer"
        ],
        "minimum_items": 32,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "frog_poem_meaning",
          "frog_life_stage_and_words",
          "frog_adaptation_reasoning",
          "frog_comparison",
          "frog_calls_and_connectors",
          "frog_sentence_sequence",
          "frog_friendly_reply",
          "frog_instruction_and_research"
        ]
      }
    ]
  }
}''')


EvidenceSpec = tuple[str, str, tuple[str, ...]]
_GUIDANCE_PATTERN = re.compile(
    r"\s*(?:include the detail the question asks for|include both details|"
    r"include all \d+ details)\.?",
    flags=re.IGNORECASE,
)


def _evidence(
    suffix: str,
    description: str,
    *aliases: str,
) -> EvidenceSpec:
    return suffix, description, aliases


def _activities() -> list[dict[str, Any]]:
    activities: list[dict[str, Any]] = []
    for level in MANIFEST["levels"]:
        activities.extend(
            [
                level["co_construct"],
                *level["guided_variants"],
                *level["independent_variants"],
                *level["transfer_variants"],
                *level["review_variants"],
                *level["support_checks"].values(),
            ]
        )
    activities.extend(MANIFEST["chapter_assessment"]["items"])
    return activities


_ACTIVITY_BY_ID = {
    activity["activity_id"]: activity for activity in _activities()
}


def _guidance(count: int) -> str:
    if count == 1:
        return "Include the detail the question asks for."
    if count == 2:
        return "Include both details."
    return f"Include all {count} details."


def _repair_open(
    activity_id: str,
    evidence: list[EvidenceSpec],
    *,
    passage: str | None = None,
    prompt: str | None = None,
    model_answer: str | None = None,
    ordered: bool | None = None,
) -> None:
    activity = _ACTIVITY_BY_ID[activity_id]
    if activity["kind"] != "open_response":
        raise ValueError(f"chapter_5_semantic_repair_requires_open:{activity_id}")
    if passage is not None:
        activity["passage"] = passage
    if prompt is not None:
        activity["prompt"] = prompt
    activity["model_answer"] = (
        model_answer
        if model_answer is not None
        else re.sub(
            r"\s+Reference evidence states:.*$",
            "",
            activity["model_answer"],
            flags=re.IGNORECASE,
        )
    )

    criteria = []
    slots = []
    for suffix, description, aliases in evidence:
        slot_id = f"{activity_id}:{suffix}"
        criteria.append(
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": 0.7,
            }
        )
        slots.append(
            {
                "id": slot_id,
                "description": description,
                "any_of": list(aliases),
            }
        )
    activity["rubric_criteria"] = criteria
    activity["concept_slots"] = slots

    ordered_ids = [criterion["id"] for criterion in criteria]
    if ordered is True or (
        ordered is None and "ordered_concept_slot_ids" in activity
    ):
        activity["ordered_concept_slot_ids"] = ordered_ids
    elif ordered is False:
        activity.pop("ordered_concept_slot_ids", None)

    teaching = _GUIDANCE_PATTERN.sub("", activity["teaching_block"]).strip()
    activity["teaching_block"] = f"{teaching} {_guidance(len(criteria))}"


_repair_open(
    "frog_life_stage_and_words:independent:2",
    [
        _evidence("meaning", "Defines larva as an early young stage.", "Larva means an early young stage"),
        _evidence("tail", "Uses the tail as one context clue.", "it has a tail"),
        _evidence("legs", "Uses the absent legs as a second context clue.", "has not grown legs"),
    ],
    model_answer=(
        "Larva means an early young stage; it has a tail and has not grown legs, "
        "showing that it has only recently hatched."
    ),
)

_repair_open(
    "frog_life_stage_and_words:independent:3",
    [
        _evidence("eggs", "Begins with eggs in jelly.", "begins with round eggs in jelly"),
        _evidence("tadpoles", "Places swimming tadpoles second.", "followed by swimming tadpoles"),
        _evidence("legs", "Places hind-leg growth third.", "Hind legs then appear"),
        _evidence("froglets", "Ends with the recorded froglet stage.", "final recorded stage is a four-legged froglet with a short tail"),
        _evidence("boundary", "Does not invent an adult stage.", "does not show an adult stage"),
    ],
    model_answer=(
        "The log begins with round eggs in jelly, followed by swimming tadpoles. "
        "Hind legs then appear, and the final recorded stage is a four-legged "
        "froglet with a short tail. The log does not show an adult stage."
    ),
    ordered=True,
)

_repair_open(
    "frog_life_stage_and_words:transfer:4",
    [
        _evidence("eggs", "Places eggs first.", "order begins with eggs"),
        _evidence("larva", "Places larva second.", "larva comes second"),
        _evidence("pupa", "Places pupa third.", "pupa follows the larva"),
        _evidence("adult", "Places the adult last.", "adult emerges last"),
        _evidence("meaning", "Defines wriggling from the movement clue.", "Wriggling means moving with repeated twists"),
        _evidence("limit", "States the missing duration fact.", "does not state how long any stage lasts"),
    ],
    model_answer=(
        "The order begins with eggs; larva comes second, pupa follows the larva, "
        "and the adult emerges last. Wriggling means moving with repeated twists "
        "below the water. The card does not state how long any stage lasts."
    ),
    ordered=True,
)

_repair_open(
    "frog_comparison:transfer:4",
    [
        _evidence("similarity", "States the shared webbed-foot swimming feature.", "Both animals swim with webbed feet"),
        _evidence("feeding", "Contrasts fish and water-plant food.", "otter catches fish, while the beaver eats water plants"),
        _evidence("habitat_use", "Contrasts their resting shelters.", "otter rests in a riverbank den, while the beaver rests in a stick lodge"),
    ],
    passage=(
        "Otter card: swims with webbed feet, catches fish in water, and rests in "
        "a riverbank den. Beaver card: swims with webbed hind feet, eats water "
        "plants, and rests in a stick lodge."
    ),
    model_answer=(
        "Both animals swim with webbed feet. The otter catches fish, while the "
        "beaver eats water plants. The otter rests in a riverbank den, while the "
        "beaver rests in a stick lodge."
    ),
)

_repair_open(
    "frog_friendly_reply:transfer:4",
    [
        _evidence("action", "Tells Iqra to report the eggs to an adult first.", "tell a teacher or another adult first"),
        _evidence("no_touch", "States the no-touch instruction.", "Do not touch the eggs"),
        _evidence("reason", "Explains the wet-habitat risk.", "moving them may damage their wet habitat"),
        _evidence("question", "Asks one connected safety question.", "Is the track close to where vehicles pass"),
        _evidence("close", "Ends with a polite close and name.", "Take care, Riya"),
    ],
)

_repair_open(
    "frog_friendly_reply:review:3",
    [
        _evidence("job", "Suggests a safe dry-bank recording job.", "record each bag of litter collected from the dry bank"),
        _evidence("reason", "Explains how the record helps later surveys.", "help the class compare future surveys"),
        _evidence("question", "Asks about the adult-marked safe area.", "Will an adult mark the safe working area"),
        _evidence("close", "Ends with a friendly close and name.", "Your friend, Kabir"),
    ],
)

_repair_open(
    "frog_friendly_reply:review:4",
    [
        _evidence("stripe", "Records the brown stripe.", "record the brown stripe"),
        _evidence("place", "Records the exact place.", "the pond-edge path"),
        _evidence("time", "Records the exact time.", "4:20 p.m."),
        _evidence("limit", "States why the species is not yet identified.", "cannot identify the species from one shared stripe"),
        _evidence("next_step", "Suggests safe adult verification.", "ask the adult nature leader to compare the full photograph"),
        _evidence("question", "Asks one connected observation question.", "Did you photograph its legs too"),
        _evidence("close", "Ends with a polite close and name.", "Best wishes, Neel"),
    ],
    passage=(
        "Hello! I photographed a frog from the pond-edge path without using "
        "flash at 4:20 p.m. It had a brown stripe, but the field guide says "
        "several species share that mark. An adult nature leader can compare the "
        "full photograph. Can I name the species now? - Tara"
    ),
    prompt=(
        "Reply in 35 to 55 words with all three record details, explain why she "
        "cannot identify the species yet, give one safe verification step, ask a "
        "related question, and close politely."
    ),
    model_answer=(
        "Hello Tara, record the brown stripe, the pond-edge path, and 4:20 p.m. "
        "You cannot identify the species from one shared stripe, so ask the adult "
        "nature leader to compare the full photograph. Did you photograph its "
        "legs too? Best wishes, Neel"
    ),
)

_repair_open(
    "frog_instruction_and_research:guided:2",
    [
        _evidence("setup", "Chooses the setting first.", "First choose the setting"),
        _evidence("frog", "Adds the frog after the setting.", "then add the frog"),
        _evidence("labels", "Labels the water and shelter.", "label the water and shelter"),
        _evidence("sentence", "Ends by writing one sentence.", "finally write one sentence"),
    ],
    ordered=True,
)

_repair_open(
    "frog_instruction_and_research:transfer:4",
    [
        _evidence("label", "Labels all three jars first.", "First label the clear jars A, B, and C"),
        _evidence("fill", "Uses an adult to fill from marked points.", "let an adult fill them at the marked points"),
        _evidence("compare", "Compares jar colour on the white tray.", "white tray and compare their colour"),
        _evidence("safety", "Preserves the no-tasting and no-touching rule.", "without tasting or touching the water"),
        _evidence("record", "Records only visible differences.", "Record only visible differences"),
        _evidence("return", "Seals and returns the jars to the adult.", "seal the jars and return them to the adult"),
    ],
    ordered=True,
)

_repair_open(
    "frog_instruction_and_research:review:3",
    [
        _evidence("fixed", "Keeps one fixed stick unmoved.", "Mark one fixed stick and keep it unmoved"),
        _evidence("times", "Traces at all three supplied times.", "At 9 a.m., noon, and 3 p.m., trace the shadow tip"),
        _evidence("labels", "Labels every traced time.", "label each time"),
        _evidence("measure", "Measures every traced line.", "Measure every traced line"),
        _evidence("limit", "Compares only recorded lengths and directions.", "Compare only the recorded shadow lengths and directions"),
    ],
    ordered=True,
)

_repair_open(
    "frog_instruction_and_research:review:4",
    [
        _evidence("animal", "Chooses one aquatic animal.", "Choose one aquatic animal"),
        _evidence("cards", "Reads two labelled fact cards.", "read two labelled fact cards"),
        _evidence("titles", "Copies both card titles.", "Copy both card titles"),
        _evidence("facts", "Lists one matching fact from each card.", "list one matching fact from each"),
        _evidence("disagreement", "Marks any disagreement.", "circle any disagreement"),
        _evidence("approval", "Asks the librarian before another source.", "Ask the librarian before adding another source"),
        _evidence("report", "Names both titles so each fact stays traceable.", "two-sentence report that names both card titles"),
    ],
    ordered=True,
)

_repair_open(
    "eng_c5_ch05_assess_a12",
    [
        _evidence("greeting", "Greets Zoya.", "Hi Zoya"),
        _evidence("answer", "Answers whether frogs are heard near school.", "I sometimes hear frogs near the drain behind our school"),
        _evidence("detail", "Adds one relevant call detail.", "deep croaks continue for several minutes"),
        _evidence("question", "Asks one related question.", "Was the sports field still wet"),
        _evidence("closing", "Includes a friendly closing.", "Your friend"),
        _evidence("name", "Includes the writer's name.", "Riya"),
    ],
    model_answer=(
        "Hi Zoya, I sometimes hear frogs near the drain behind our school on wet "
        "afternoons after rain. Their deep croaks continue for several minutes. "
        "Was the sports field still wet when you heard them? Your friend, Riya"
    ),
)

_repair_open(
    "eng_c5_ch05_assess_a13",
    [
        _evidence("cut", "Begins with adult cutting help.", "ask an adult to cut the bottle top"),
        _evidence("funnel", "Turns the top into a funnel.", "turn the top upside down as a funnel"),
        _evidence("marks", "Adds equal centimetre marks.", "Mark equal centimetre lines"),
        _evidence("placement", "Places the bottle in an open area.", "place the bottle in an open area"),
        _evidence("measure", "Reads the water at eye level after rain.", "After rain, read at eye level"),
        _evidence("reason", "Explains the eye-level accuracy reason.", "for a more accurate measurement"),
        _evidence("record", "Records the amount and empties the bottle.", "Record the amount and empty the bottle"),
    ],
    ordered=True,
)

_repair_open(
    "eng_c5_ch05_assess_b12",
    [
        _evidence("greeting", "Greets Arjun.", "Hi Arjun"),
        _evidence("answer", "Answers the small-animal question.", "I saw a small snail beside our school garden"),
        _evidence("detail", "Adds a relevant observation detail.", "moved slowly under a wet leaf"),
        _evidence("question", "Asks one connected question.", "What colour was the frog"),
        _evidence("closing", "Includes a friendly closing.", "Best wishes"),
        _evidence("name", "Includes the writer's name.", "Kabir"),
    ],
    prompt=(
        "Write Arjun a 35 to 55 word reply with a greeting, direct answer, "
        "observation detail, connected question, closing, and name."
    ),
    model_answer=(
        "Hi Arjun, I saw a small snail beside our school garden after rain last "
        "week one afternoon. It moved slowly under a wet leaf. What colour was the "
        "frog in your rain garden? Best wishes, Kabir"
    ),
)

_repair_open(
    "eng_c5_ch05_assess_b13",
    [
        _evidence("fold", "Folds the paper towel first.", "Fold the paper towel"),
        _evidence("dampen", "Dampens the towel.", "dampen the paper towel"),
        _evidence("bean", "Places one bean inside.", "place one bean inside it"),
        _evidence("pouch", "Slides the towel into a clear pouch.", "Slide the towel into a clear pouch"),
        _evidence("seal", "Seals the pouch.", "seal it"),
        _evidence("date", "Labels the date.", "Label the date"),
        _evidence("observe", "Ends with the repeating daily observation.", "observe the bean daily"),
    ],
    model_answer=(
        "Fold the paper towel and dampen the paper towel, then place one bean "
        "inside it. Slide the towel into a clear pouch and seal it. Label the date "
        "and observe the bean daily."
    ),
    ordered=True,
)
