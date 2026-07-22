"""Authored deep manifest for Class 5 English Chapter 4.

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
    "chapter_id": "eng_c5_ch04",
    "chapter_no": 4,
    "title": "The Wise Parrot",
    "book_title": "Santoor",
    "unit_title": "My Colourful World",
    "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf",
    "source_note": "NCERT structural alignment only. All teaching passages, prompts, examples, answers, and rubrics are original Zidd-authored content and do not copy the textbook body.",
    "content_version": "2026-07-15.5",
    "certification_version": "2026-07-15.5",
    "authorship": {
      "zidd_authored_original": true,
      "textbook_body_or_questions_copied": false,
      "source_analysis_reference": "agent-reviewed official structural exercise matrix for eng_c5_ch04"
    }
  },
  "source_anchors": [
    {
      "anchor_id": "eng_c5_ch04:read:1-4",
      "section_label": "Let us Read",
      "page_start": 1,
      "page_end": 4,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=1",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch04:think:5",
      "section_label": "Let us Think",
      "page_start": 5,
      "page_end": 5,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=5",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch04:learn:6-8",
      "section_label": "Let us Learn",
      "page_start": 6,
      "page_end": 8,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=6",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch04:listen:8",
      "section_label": "Let us Listen",
      "page_start": 8,
      "page_end": 8,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=8",
      "coverage_treatment": "guided_only",
      "required_for_chapter_certification": false
    },
    {
      "anchor_id": "eng_c5_ch04:speak:9",
      "section_label": "Let us Speak",
      "page_start": 9,
      "page_end": 9,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=9",
      "coverage_treatment": "textbook_companion",
      "required_for_chapter_certification": false
    },
    {
      "anchor_id": "eng_c5_ch04:write:10",
      "section_label": "Let us Write",
      "page_start": 10,
      "page_end": 10,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=10",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch04:do:10-11",
      "section_label": "Let us Do",
      "page_start": 10,
      "page_end": 11,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=10",
      "coverage_treatment": "textbook_companion",
      "required_for_chapter_certification": false
    },
    {
      "anchor_id": "eng_c5_ch04:explore:12",
      "section_label": "Let us Explore",
      "page_start": 12,
      "page_end": 12,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=12",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch04:self_assessment:13-14",
      "section_label": "Self-assessment",
      "page_start": 13,
      "page_end": 14,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa104.pdf#page=13",
      "coverage_treatment": "guided_only",
      "required_for_chapter_certification": false
    }
  ],
  "levels": [
    {
      "level_id": "wise_parrot_story_sequence",
      "title": "Track the message and escape",
      "focus": "sequence events and attribute dialogue accurately",
      "outcome": "Place the message, signal, copied action, and release in order while naming the correct speaker for each key line.",
      "skill_ids": [
        "reading.event_sequence",
        "reading.dialogue_attribution",
        "reading.sentence_comprehension"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch04:read:1-4",
        "eng_c5_ch04:think:5"
      ],
      "connect": {
        "teaching_block": "An escape plan becomes clear when each message, observed action, copied action, and consequence is placed in causal order.",
        "passage": "A child sends a note, a friend demonstrates a silent signal, the child copies it, and a locked door is opened. The signal matters only because the events connect.",
        "prompt": "Continue when you can explain how this example helps you sequence events and attribute dialogue accurately."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "wise_parrot_story_sequence:co_construct",
        "teaching_block": "Track the actor, spoken message, and next event in the chain. Locate the exact clue before comparing the choices.",
        "passage": "Before a trip, a shopkeeper agrees to carry a caged bird's greeting to a forest flock.",
        "prompt": "What is the first event in this message chain?",
        "skill_ids": [
          "reading.event_sequence",
          "reading.dialogue_attribution",
          "reading.sentence_comprehension"
        ],
        "options": [
          "the shopkeeper promises to carry the greeting",
          "the forest bird opens the cage",
          "the caged bird returns from the forest",
          "the flock asks for a golden cage"
        ],
        "accepted_answers": [
          "the shopkeeper promises to carry the greeting"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:guided:1",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Read the whole sentence, then test every option against its meaning.",
          "passage": "A forest parrot hears the greeting and immediately lies still beneath its tree.",
          "prompt": "Which event follows the greeting?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the trader buys fruit",
            "the forest parrot lies still",
            "the pet bird sings loudly",
            "the cage door breaks"
          ],
          "accepted_answers": [
            "the forest parrot lies still"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:guided:2",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Track who or what each detail belongs to before deciding.",
          "passage": "The captive bird says, 'Please greet the forest flock for me.'",
          "prompt": "Who is speaking, and who is being addressed?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the forest flock speaks to the captive bird",
            "the trader speaks to the forest flock",
            "the captive bird speaks to the trader",
            "the trader speaks to the captive bird"
          ],
          "accepted_answers": [
            "the captive bird speaks to the trader"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:guided:3",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "At home, the traveller reports that a forest bird became motionless. The pet then becomes still too.",
          "prompt": "Which event happens immediately after the report?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the pet becomes still",
            "the traveller begins the journey",
            "the forest flock sends fruit",
            "the cage is carried to the forest"
          ],
          "accepted_answers": [
            "the pet becomes still"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:guided:4",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Reject any option that adds a fact the passage never gives.",
          "passage": "'My friend showed me what to do,' the freed bird says after spreading its wings.",
          "prompt": "What does this line explain?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "why the trader travelled",
            "why the cage was valuable",
            "how the bird understood the silent signal",
            "how the forest became quiet"
          ],
          "accepted_answers": [
            "how the bird understood the silent signal"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:independent:1",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Build the answer from two visible pieces of evidence.",
          "passage": "A courier repeats a bird's greeting in the grove. One bird becomes still. Back home, the caged bird hears the report and copies the action.",
          "prompt": "State the middle two events in order and explain their connection.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wild_signal",
              "description": "Names the forest bird's still signal.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "copied_signal",
              "description": "Names the captive bird's copied action after hearing the report.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wild_signal",
              "description": "Names the forest bird's still signal.",
              "any_of": [
                "forest bird became still",
                "bird lay motionless"
              ]
            },
            {
              "id": "copied_signal",
              "description": "Names the captive bird's copied action after hearing the report.",
              "any_of": [
                "caged bird copied",
                "captive bird became still"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "forest",
            "bird",
            "became",
            "still",
            "motionless"
          ],
          "model_answer": "The forest bird first became still as a signal; after hearing the report, the captive bird copied that still pose. Reference evidence states: forest bird became still; caged bird copied.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "wild_signal",
            "copied_signal"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:independent:2",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. State the relationship and support it with the relevant detail.",
          "passage": "'Carry my greeting,' says the caged bird. Later the traveller says, 'A forest bird fell still when it heard your message.'",
          "prompt": "Attribute both lines to their speakers and explain what the second line supplies.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "first_speaker",
              "description": "Attributes the request to the caged bird.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "second_speaker",
              "description": "Attributes the report to the traveller.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "report_clue",
              "description": "Explains that the report supplies the escape clue.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "first_speaker",
              "description": "Attributes the request to the caged bird.",
              "any_of": [
                "caged bird asks",
                "bird says carry my greeting"
              ]
            },
            {
              "id": "second_speaker",
              "description": "Attributes the report to the traveller.",
              "any_of": [
                "traveller reports",
                "keeper tells the bird"
              ]
            },
            {
              "id": "report_clue",
              "description": "Explains that the report supplies the escape clue.",
              "any_of": [
                "supplies the clue",
                "shows the still signal"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "caged",
            "bird",
            "asks",
            "says",
            "carry"
          ],
          "model_answer": "The caged bird asks the traveller to carry its greeting. The traveller later reports the forest bird's still action, which supplies the clue. Reference evidence states: traveller reports.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:independent:3",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Explain the first part before connecting it to the result.",
          "passage": "A bird receives a distant signal, waits for its keeper's report, copies the signal, and is lifted through an open door.",
          "prompt": "Summarise the four-part plan in the correct order.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "receive",
              "description": "Includes receipt of the distant signal.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "copy",
              "description": "Includes copying the signal after the report.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "release",
              "description": "Includes being moved outside the open cage.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "escape",
              "description": "Ends with the bird escaping.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "receive",
              "description": "Includes receipt of the distant signal.",
              "any_of": [
                "receives a distant signal",
                "hears the reported signal"
              ]
            },
            {
              "id": "copy",
              "description": "Includes copying the signal after the report.",
              "any_of": [
                "copies the signal",
                "becomes still"
              ]
            },
            {
              "id": "release",
              "description": "Includes being moved outside the open cage.",
              "any_of": [
                "lifted outside",
                "keeper opens the cage"
              ]
            },
            {
              "id": "escape",
              "description": "Ends with the bird escaping.",
              "any_of": [
                "flies away",
                "escapes"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "receives",
            "distant",
            "signal",
            "hears",
            "reported"
          ],
          "model_answer": "The bird hears the reported signal, becomes still, is lifted outside the opened cage, and then flies away.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "receive",
            "copy",
            "release",
            "escape"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:independent:4",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Use your own words while preserving every required idea.",
          "passage": "Amina says, 'Show me a sign when the hall is clear.' Rohan later switches off the porch lamp. Amina sees the signal and leaves quietly.",
          "prompt": "Who gives the instruction, who performs the signal, and what happens last?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "instruction_speaker",
              "description": "Names Amina as the person giving the instruction.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "signal_actor",
              "description": "Names Rohan as the person performing the signal.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "last_event",
              "description": "States that Amina leaves after seeing it.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "instruction_speaker",
              "description": "Names Amina as the person giving the instruction.",
              "any_of": [
                "Amina gives",
                "Amina asks"
              ]
            },
            {
              "id": "signal_actor",
              "description": "Names Rohan as the person performing the signal.",
              "any_of": [
                "Rohan switches",
                "Rohan gives the signal"
              ]
            },
            {
              "id": "last_event",
              "description": "States that Amina leaves after seeing it.",
              "any_of": [
                "Amina leaves",
                "she leaves quietly"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 14,
          "relevance_terms": [
            "amina",
            "gives",
            "asks",
            "rohan",
            "switches"
          ],
          "model_answer": "Amina gives the instruction, Rohan gives the signal by switching off the porch lamp, and Amina leaves quietly after seeing it.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "instruction_speaker",
            "signal_actor",
            "last_event"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:transfer:1",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Apply the same reasoning to a different setting and justify it.",
          "passage": "A puppy scratches twice at the gate. Dev hears it, unlatches the gate, and the puppy runs to its owner.",
          "prompt": "Explain this as signal, response, and result.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "signal",
              "description": "Identifies the puppy's scratching as the signal.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "response",
              "description": "Identifies Dev's response.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Identifies the reunion result.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "signal",
              "description": "Identifies the puppy's scratching as the signal.",
              "any_of": [
                "puppy scratches",
                "scratches twice"
              ]
            },
            {
              "id": "response",
              "description": "Identifies Dev's response.",
              "any_of": [
                "Dev unlatches",
                "opens the gate"
              ]
            },
            {
              "id": "result",
              "description": "Identifies the reunion result.",
              "any_of": [
                "runs to its owner",
                "puppy reaches owner"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 14,
          "relevance_terms": [
            "puppy",
            "scratches",
            "twice",
            "unlatches",
            "opens"
          ],
          "model_answer": "The puppy scratches twice as the signal, Dev unlatches the gate in response, and the puppy runs to its owner.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "signal",
            "response",
            "result"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:transfer:2",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Separate what is stated from what can reasonably be inferred.",
          "passage": "A librarian tells Mina, 'Place the blue card on the desk when you need help.' Mina places it there, and the librarian comes over.",
          "prompt": "Track the instruction, action, and response without changing the speaker.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "instruction",
              "description": "Attributes the instruction to the librarian.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "States that Mina places the card.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "response",
              "description": "States that the librarian comes to help.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "instruction",
              "description": "Attributes the instruction to the librarian.",
              "any_of": [
                "librarian tells",
                "librarian gives the instruction"
              ]
            },
            {
              "id": "action",
              "description": "States that Mina places the card.",
              "any_of": [
                "Mina places",
                "blue card on the desk"
              ]
            },
            {
              "id": "response",
              "description": "States that the librarian comes to help.",
              "any_of": [
                "librarian comes",
                "comes over to help"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "librarian",
            "tells",
            "gives",
            "instruction",
            "mina"
          ],
          "model_answer": "The librarian gives the instruction, Mina places the blue card on the desk, and the librarian responds by coming to help. Reference evidence states: librarian comes.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "instruction",
            "action",
            "response"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:transfer:3",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Organise the response so each required point has a clear role.",
          "passage": "A cyclist rings a bell, a walker moves to the side, and the cyclist passes safely.",
          "prompt": "Write the three events in order and explain why the middle event matters.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "bell",
              "description": "Begins with the cyclist ringing the bell.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "walker_moves",
              "description": "Places the walker's movement second.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safe_result",
              "description": "Ends with safe passage and links it to the movement.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "bell",
              "description": "Begins with the cyclist ringing the bell.",
              "any_of": [
                "cyclist rings",
                "bell sounds"
              ]
            },
            {
              "id": "walker_moves",
              "description": "Places the walker's movement second.",
              "any_of": [
                "walker moves aside",
                "moves to the side"
              ]
            },
            {
              "id": "safe_result",
              "description": "Ends with safe passage and links it to the movement.",
              "any_of": [
                "passes safely",
                "space allows safe passing"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 14,
          "relevance_terms": [
            "cyclist",
            "rings",
            "bell",
            "sounds",
            "walker"
          ],
          "model_answer": "The cyclist rings the bell, the walker moves aside to create space, and the cyclist then passes safely.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "bell",
            "walker_moves",
            "safe_result"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:transfer:4",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Use precise vocabulary instead of a vague general statement.",
          "passage": "'Wait for my whistle,' says Coach Mira. Kabir hears the whistle, begins his run, and crosses the finish line.",
          "prompt": "Identify the speaker and sequence the athlete's next two actions.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "coach_speaker",
              "description": "Names Coach Mira as the speaker.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "start",
              "description": "States that Kabir begins after hearing the whistle.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "finish",
              "description": "States that he crosses the finish line last.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "coach_speaker",
              "description": "Names Coach Mira as the speaker.",
              "any_of": [
                "Coach Mira says",
                "coach gives the instruction"
              ]
            },
            {
              "id": "start",
              "description": "States that Kabir begins after hearing the whistle.",
              "any_of": [
                "Kabir begins",
                "starts after the whistle"
              ]
            },
            {
              "id": "finish",
              "description": "States that he crosses the finish line last.",
              "any_of": [
                "crosses the finish line",
                "finishes the run"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 13,
          "relevance_terms": [
            "coach",
            "mira",
            "says",
            "gives",
            "instruction"
          ],
          "model_answer": "Coach Mira says to wait for her whistle. Kabir begins after the whistle and finally crosses the finish line.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "coach_speaker",
            "start",
            "finish"
          ]
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:review:1",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Retrieve the skill after a delay and make the evidence explicit.",
          "passage": "The forest signal is reported at home. The pet copies it. The keeper moves the pet outside. The pet reveals it is alive.",
          "prompt": "Retrieve the sequence and state which event proves the plan worked.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "ordered_chain",
              "description": "Preserves report, copy, release, and reveal in order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "proof",
              "description": "Identifies the pet revealing life or flying as proof.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "ordered_chain",
              "description": "Preserves report, copy, release, and reveal in order.",
              "any_of": [
                "report then copy",
                "reported at home before it copied"
              ]
            },
            {
              "id": "proof",
              "description": "Identifies the pet revealing life or flying as proof.",
              "any_of": [
                "reveals it is alive",
                "flies away proves"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 16,
          "relevance_terms": [
            "report",
            "then",
            "copy",
            "reported",
            "home"
          ],
          "model_answer": "After the signal was reported, the pet copied it and was moved outside; opening its eyes and flying proved the plan worked. Reference evidence states: report then copy; reveals it is alive.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "ordered_chain",
            "proof"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:review:2",
          "teaching_block": "Reconstruct the chain without changing who spoke or when each action happened. Check the final response for meaning, completeness, and support.",
          "passage": "A note says, 'Tap once when the door is unlocked.' Nila taps, Omar opens the cupboard, and the class retrieves its art box.",
          "prompt": "Name the instruction's speaker if it is not stated, then separate what is known from what is unknown.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "known_events",
              "description": "States the known signal, response, and result.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "unknown_speaker",
              "description": "States that the note's writer is not identified.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "known_events",
              "description": "States the known signal, response, and result.",
              "any_of": [
                "Nila taps",
                "Omar opens",
                "class retrieves"
              ]
            },
            {
              "id": "unknown_speaker",
              "description": "States that the note's writer is not identified.",
              "any_of": [
                "writer is unknown",
                "speaker is not stated"
              ]
            }
          ],
          "forbidden_phrases": [
            "Nila wrote the note",
            "Omar wrote the note"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "nila",
            "taps",
            "omar",
            "opens",
            "class"
          ],
          "model_answer": "The writer of the note is not identified. What is known is that Nila taps, Omar opens the cupboard, and the class retrieves the art box. Reference evidence states: writer is unknown.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:review:3",
          "teaching_block": "Track who communicates, what happens next, and how the final event follows from the signal. Retrieve the construct, then verify it against the passage. Use the visible passage to practise event sequence and dialogue attribution and sentence comprehension; include both details.",
          "passage": "Coach Lata says, 'Raise the red flag after the final runner crosses.' Amir watches the last runner finish, lifts the flag, and the timekeeper stops the clock.",
          "prompt": "Identify the speaker and place the instruction, observed event, action, and result in order.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_story_sequence:review:3:speaker",
              "description": "Names the person who gives the instruction.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_story_sequence:review:3:sequence",
              "description": "Orders the observed event, flag action, and result.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_story_sequence:review:3:speaker",
              "description": "Names the person who gives the instruction.",
              "any_of": [
                "Coach Lata is the speaker"
              ]
            },
            {
              "id": "wise_parrot_story_sequence:review:3:sequence",
              "description": "Orders the observed event, flag action, and result.",
              "any_of": [
                "sees the final runner cross",
                "raises the red flag",
                "timekeeper stops the clock"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "coach",
            "speaker",
            "first"
          ],
          "model_answer": "Coach Lata is the speaker. First she gives the instruction, then Amir sees the final runner cross, raises the red flag, and the timekeeper stops the clock.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "wise_parrot_story_sequence:review:3:speaker",
            "wise_parrot_story_sequence:review:3:sequence"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_sequence:review:4",
          "teaching_block": "Track who communicates, what happens next, and how the final event follows from the signal. Retrieve the construct, then verify it against the passage. Use the visible passage to practise event sequence and dialogue attribution and sentence comprehension; include both details.",
          "passage": "Farid writes, 'Switch off the pump when the water reaches the blue line.' Sima sees the level touch the mark, turns off the switch, and the tank stops filling.",
          "prompt": "Name the message writer and explain how each later event follows from the instruction.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_story_sequence:review:4:writer",
              "description": "Attributes the written instruction to Farid.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_story_sequence:review:4:events",
              "description": "Connects the mark, switch action, and stopped filling.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_story_sequence:review:4:writer",
              "description": "Attributes the written instruction to Farid.",
              "any_of": [
                "Farid writes the message"
              ]
            },
            {
              "id": "wise_parrot_story_sequence:review:4:events",
              "description": "Connects the mark, switch action, and stopped filling.",
              "any_of": [
                "water reach the blue line",
                "turns off the pump",
                "tank stops filling"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "farid",
            "writes",
            "message"
          ],
          "model_answer": "Farid writes the message. Sima first sees the water reach the blue line, then turns off the pump, so the tank stops filling as instructed.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "wise_parrot_story_sequence:review:4:writer",
            "wise_parrot_story_sequence:review:4:events"
          ]
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "sequence-or-speaker-guess",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "misconception": "The learner recalls isolated events or assigns a line to a nearby character without tracking the causal order and speaker evidence.",
          "remediation": "Use an event strip and a speaker-listener-purpose table, then rebuild the chain one verified link at a time.",
          "support_check_ids": [
            "wise_parrot_story_sequence:support:bridge",
            "wise_parrot_story_sequence:support:masterclass",
            "wise_parrot_story_sequence:support:revision_level_1",
            "wise_parrot_story_sequence:support:revision_level_2",
            "wise_parrot_story_sequence:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:support:bridge",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Break the task into one smaller decision and check it carefully.",
          "passage": "The traveller sees the pet lying still, opens the door, and places it on a ledge.",
          "prompt": "Which action creates the opportunity to escape?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "seeing the forest",
            "opening the cage door",
            "repeating the greeting",
            "buying a ledge"
          ],
          "accepted_answers": [
            "opening the cage door"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:support:masterclass",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Name the rule first, then apply it to this new example.",
          "passage": "Signal: a wild bird lies still. Response: the captive bird copies it. Result: the keeper opens the cage.",
          "prompt": "Which part is the copied response?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the keeper opens the cage",
            "the flock receives a greeting",
            "the captive bird lies still",
            "the traveller enters the forest"
          ],
          "accepted_answers": [
            "the captive bird lies still"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:support:revision_level_1",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Compare the tempting error with the evidence that corrects it.",
          "passage": "The keeper says, 'I cannot let you go; ask for something else.'",
          "prompt": "Who refuses the request for freedom?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the keeper",
            "the captive bird",
            "the forest parrot",
            "the flock"
          ],
          "accepted_answers": [
            "the keeper"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:support:revision_level_2",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Use the nearby context to remove an unsupported interpretation.",
          "passage": "Once placed outside the cage, the bird opens its eyes and flies beyond reach.",
          "prompt": "What is the final result of the plan?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the bird returns to its perch",
            "the bird escapes into the open sky",
            "the traveller locks the cage",
            "the flock enters the house"
          ],
          "accepted_answers": [
            "the bird escapes into the open sky"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_sequence:support:revision_level_3",
          "teaching_block": "Track the actor, spoken message, and next event in the chain. Verify the selected answer by reading it back with the passage.",
          "passage": "Order cards: report the signal; copy the still pose; open the cage; fly away.",
          "prompt": "Which card must come directly before 'open the cage'?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.dialogue_attribution",
            "reading.sentence_comprehension"
          ],
          "options": [
            "fly away",
            "report the signal",
            "copy the still pose",
            "begin the journey"
          ],
          "accepted_answers": [
            "copy the still pose"
          ]
        }
      }
    },
    {
      "level_id": "wise_parrot_freedom_reason",
      "title": "Judge freedom and wisdom with evidence",
      "focus": "separate stated evidence from fair inference",
      "outcome": "Give a defensible judgement about freedom, intelligence, or wisdom using a stated action and a clearly marked inference.",
      "skill_ids": [
        "reading.inference_reason",
        "writing.reason_answer"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch04:read:1-4",
        "eng_c5_ch04:think:5"
      ],
      "connect": {
        "teaching_block": "A fair inference begins with an observable action, then explains what that action reasonably suggests without inventing an unstated motive.",
        "passage": "The bird repeatedly asks to fly and watches the open sky. Those details support a wish for freedom; they do not prove every thought the bird may have.",
        "prompt": "Continue when you can explain how this example helps you separate stated evidence from fair inference."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "wise_parrot_freedom_reason:co_construct",
        "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Locate the exact clue before comparing the choices.",
        "passage": "A bird receives fruit and clean water but repeatedly asks to leave its cage.",
        "prompt": "Which inference is best supported?",
        "skill_ids": [
          "reading.inference_reason"
        ],
        "options": [
          "the bird dislikes every fruit",
          "the bird values freedom despite comfort",
          "the bird wants a larger water bowl",
          "the bird plans to sell the cage"
        ],
        "accepted_answers": [
          "the bird values freedom despite comfort"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_freedom_reason:guided:1",
          "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Read the whole sentence, then test every option against its meaning.",
          "passage": "A wild parrot cannot unlock a distant cage, so it demonstrates an action the captive bird can copy.",
          "prompt": "Why is this evidence of intelligence?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "the bird uses a usable indirect clue",
            "the bird is physically larger",
            "the captive bird had already learned the action",
            "the bird speaks the loudest"
          ],
          "accepted_answers": [
            "the bird uses a usable indirect clue"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_freedom_reason:guided:2",
          "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Track who or what each detail belongs to before deciding.",
          "passage": "The captive bird waits until it is outside the cage before moving.",
          "prompt": "What does the timing reasonably suggest?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "it forgot how to move",
            "it chose a safer moment to reveal the plan",
            "it wanted the keeper to buy a window",
            "it preferred the ledge to the sky"
          ],
          "accepted_answers": [
            "it chose a safer moment to reveal the plan"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_freedom_reason:guided:3",
          "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "A keeper says the cage is safe; the bird asks for open sky.",
          "prompt": "Which statement represents both viewpoints fairly?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "both value only the cage's colour",
            "the keeper values control and safety while the bird values freedom",
            "the bird wants danger and the keeper wants travel",
            "neither character has a clear preference"
          ],
          "accepted_answers": [
            "the keeper values control and safety while the bird values freedom"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:guided:4",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "The captive bird waits until the cage is open before moving.",
          "prompt": "Complete a two-sentence reason: state what this timing suggests and cite the action that supports it.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "timing_judgement",
              "description": "States that the bird chose a careful or strategic moment.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "timing_evidence",
              "description": "Uses waiting until the cage opened as evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "timing_judgement",
              "description": "States that the bird chose a careful or strategic moment.",
              "any_of": [
                "careful moment",
                "strategic timing"
              ]
            },
            {
              "id": "timing_evidence",
              "description": "Uses waiting until the cage opened as evidence.",
              "any_of": [
                "waited until the cage opened",
                "did not move before release"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 13,
          "relevance_terms": [
            "careful",
            "moment",
            "strategic",
            "timing",
            "waited"
          ],
          "model_answer": "The timing suggests that the bird acted strategically. It waited until the cage was open before revealing that it could move. Reference evidence states: careful moment; waited until the cage opened.",
          "pass_score": 0.8
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:independent:1",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Build the answer from two visible pieces of evidence.",
          "passage": "The captive bird asks more than once to fly, even though it receives food and care.",
          "prompt": "Explain what the repeated request suggests and cite the supporting detail.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "judgement",
              "description": "States that the bird values or wants freedom.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Uses the repeated request despite care as evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "judgement",
              "description": "States that the bird values or wants freedom.",
              "any_of": [
                "wants freedom",
                "values open flight"
              ]
            },
            {
              "id": "evidence",
              "description": "Uses the repeated request despite care as evidence.",
              "any_of": [
                "asks more than once",
                "despite food and care"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "wants",
            "freedom",
            "values",
            "open",
            "flight"
          ],
          "model_answer": "The repeated request suggests that the bird values freedom, because it still asks to fly even while receiving food and care. Reference evidence states: wants freedom; asks more than once.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:independent:2",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. State the relationship and support it with the relevant detail.",
          "passage": "The wild bird sends a silent demonstration instead of an instruction that the keeper might understand.",
          "prompt": "Why is the demonstration a sensible strategy?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "strategy",
              "description": "Explains that the signal can be copied without openly revealing the plan.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "constraint",
              "description": "Recognises that the wild bird cannot directly open the distant cage.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "strategy",
              "description": "Explains that the signal can be copied without openly revealing the plan.",
              "any_of": [
                "copied without revealing",
                "silent signal hides the plan"
              ]
            },
            {
              "id": "constraint",
              "description": "Recognises that the wild bird cannot directly open the distant cage.",
              "any_of": [
                "cannot open the cage",
                "is far away"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "copied",
            "without",
            "revealing",
            "silent",
            "signal"
          ],
          "model_answer": "The wild bird cannot open the distant cage, so it sends a silent action the captive bird can copy without openly revealing the plan. Reference evidence states: copied without revealing; cannot open the cage.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:independent:3",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Explain the first part before connecting it to the result.",
          "passage": "The captive bird stays motionless until the keeper places it outside.",
          "prompt": "What does this timing show about the bird's judgement?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "timing",
              "description": "Names waiting until outside as the key timing choice.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains that moving earlier could stop the escape.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "timing",
              "description": "Names waiting until outside as the key timing choice.",
              "any_of": [
                "waits until outside",
                "stays still until released"
              ]
            },
            {
              "id": "reason",
              "description": "Explains that moving earlier could stop the escape.",
              "any_of": [
                "moving earlier would stop",
                "safer to wait"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "waits",
            "until",
            "outside",
            "stays",
            "still"
          ],
          "model_answer": "The bird shows good judgement by waiting until it is outside, because moving earlier could make the keeper close the cage again. Reference evidence states: waits until outside; moving earlier would stop.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:independent:4",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Use your own words while preserving every required idea.",
          "passage": "A classmate says only the wild parrot is wise. Another says only the captive parrot is wise.",
          "prompt": "Give a more balanced judgement using one contribution from each bird.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wild_contribution",
              "description": "Credits the wild bird with devising or sending the clue.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "captive_contribution",
              "description": "Credits the captive bird with interpreting and timing the action.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wild_contribution",
              "description": "Credits the wild bird with devising or sending the clue.",
              "any_of": [
                "wild bird devises",
                "sends the clue"
              ]
            },
            {
              "id": "captive_contribution",
              "description": "Credits the captive bird with interpreting and timing the action.",
              "any_of": [
                "captive bird interprets",
                "acts at the right time"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 17,
          "relevance_terms": [
            "wild",
            "bird",
            "devises",
            "sends",
            "clue"
          ],
          "model_answer": "The wild parrot is wise for creating the clue, while the captive parrot is wise for interpreting it and acting at the right time. Reference evidence states: wild bird devises; captive bird interprets.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:transfer:1",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Apply the same reasoning to a different setting and justify it.",
          "passage": "A rehabilitated heron can feed itself, but a busy road separates the centre from its wetland.",
          "prompt": "Recommend a fair next step and justify it from both facts.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "recommendation",
              "description": "Recommends an expert-planned safe release rather than immediate handling.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "two_facts",
              "description": "Uses both self-feeding and road risk.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "recommendation",
              "description": "Recommends an expert-planned safe release rather than immediate handling.",
              "any_of": [
                "expert planned release",
                "wait for a safe release"
              ]
            },
            {
              "id": "two_facts",
              "description": "Uses both self-feeding and road risk.",
              "any_of": [
                "can feed itself",
                "busy road is a risk"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "expert",
            "planned",
            "release",
            "wait",
            "safe"
          ],
          "model_answer": "The centre should plan a safe release with experts: the heron can feed itself, but the busy road makes an immediate release risky. Reference evidence states: expert planned release.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:transfer:2",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Separate what is stated from what can reasonably be inferred.",
          "passage": "A child finds a nestling on a low branch. It is alert, feathered, and watched by an adult bird nearby.",
          "prompt": "What is the most responsible inference and action?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "inference",
              "description": "Infers that the adult may still be caring for the young bird.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Recommends observing from a distance or contacting a trained rescuer if danger appears.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "inference",
              "description": "Infers that the adult may still be caring for the young bird.",
              "any_of": [
                "adult may be caring",
                "parent is nearby"
              ]
            },
            {
              "id": "action",
              "description": "Recommends observing from a distance or contacting a trained rescuer if danger appears.",
              "any_of": [
                "observe from a distance",
                "contact a trained rescuer"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "adult",
            "caring",
            "parent",
            "nearby",
            "observe"
          ],
          "model_answer": "Because an adult bird is nearby, the young bird may still be under care; the child should observe from a distance and seek expert help only if it is in danger. Reference evidence states: adult may be caring.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:transfer:3",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Organise the response so each required point has a clear role.",
          "passage": "A powerful dog pulls at a gate, while a smaller dog nudges the latch upward with its nose.",
          "prompt": "Explain how the scene distinguishes strength from intelligent action.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "strength",
              "description": "Identifies pulling as force without solving the latch.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "intelligence",
              "description": "Identifies the latch action as understanding the mechanism.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "strength",
              "description": "Identifies pulling as force without solving the latch.",
              "any_of": [
                "pulling uses force",
                "power does not open latch"
              ]
            },
            {
              "id": "intelligence",
              "description": "Identifies the latch action as understanding the mechanism.",
              "any_of": [
                "nudges the latch",
                "understands how it opens"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "pulling",
            "uses",
            "force",
            "power",
            "does"
          ],
          "model_answer": "The larger dog uses force by pulling, but the smaller dog solves the problem by lifting the latch mechanism with its nose. Reference evidence states: pulling uses force; nudges the latch.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:transfer:4",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Use precise vocabulary instead of a vague general statement.",
          "passage": "The story states that the keeper loves the bird and refuses to release it. It does not state why the cage is made of gold.",
          "prompt": "Write one supported inference and one detail that must remain unknown.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "supported",
              "description": "Infers attachment or unwillingness to lose the bird from the refusal.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "unknown",
              "description": "Keeps the original reason for the golden cage unknown.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "supported",
              "description": "Infers attachment or unwillingness to lose the bird from the refusal.",
              "any_of": [
                "attached to the bird",
                "does not want to lose it"
              ]
            },
            {
              "id": "unknown",
              "description": "Keeps the original reason for the golden cage unknown.",
              "any_of": [
                "reason for gold is unknown",
                "motive is not stated"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "attached",
            "bird",
            "does",
            "want",
            "lose"
          ],
          "model_answer": "The refusal suggests that the keeper is attached to the bird, but the reason for choosing a golden cage is not stated. Reference evidence states: reason for gold is unknown.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:review:1",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Retrieve the skill after a delay and make the evidence explicit.",
          "passage": "A recovered owl is alert and can fly, but a wing check has not yet been completed.",
          "prompt": "Should it be released now? Give an evidence-based reason.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "decision",
              "description": "Recommends waiting for the remaining expert check.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Balances signs of recovery with missing evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "decision",
              "description": "Recommends waiting for the remaining expert check.",
              "any_of": [
                "wait for the wing check",
                "not release yet"
              ]
            },
            {
              "id": "evidence",
              "description": "Balances signs of recovery with missing evidence.",
              "any_of": [
                "can fly but check incomplete",
                "recovery signs and missing check"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "wait",
            "wing",
            "check",
            "release",
            "incomplete"
          ],
          "model_answer": "The owl should not be released yet: it can fly, but the incomplete wing check means its readiness is not fully confirmed. Reference evidence states: wait for the wing check; can fly but check incomplete.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:review:2",
          "teaching_block": "State the judgement, cite the visible evidence, and explain the reasonable link between them. Check the final response for meaning, completeness, and support.",
          "passage": "Two parrots solve one problem: one communicates an idea and the other carries it out without force.",
          "prompt": "Explain why the solution can be called wise.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "communication",
              "description": "Names the useful communicated idea.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "execution",
              "description": "Names interpretation and timely action without force.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "communication",
              "description": "Names the useful communicated idea.",
              "any_of": [
                "communicates a useful idea",
                "sends a clue"
              ]
            },
            {
              "id": "execution",
              "description": "Names interpretation and timely action without force.",
              "any_of": [
                "interprets and acts",
                "uses timing instead of force"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "communicates",
            "useful",
            "idea",
            "sends",
            "clue"
          ],
          "model_answer": "The solution is wise because one bird communicates a usable clue and the other interprets and carries it out at the right time without force. Reference evidence states: communicates a useful idea; interprets and acts.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:review:3",
          "teaching_block": "Separate stated evidence from inference, then justify a responsible judgement with the supplied facts. Retrieve the construct, then verify it against the passage. Use the visible passage to practise inference reason and reason answer; include both details.",
          "passage": "A rescued kite can glide across the enclosure, but strong winds are forecast and its release field has no shelter.",
          "prompt": "Recommend whether release should happen today and support the decision with both facts.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_freedom_reason:review:3:decision",
              "description": "Gives a clear release recommendation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_freedom_reason:review:3:evidence",
              "description": "Uses the wind and shelter facts while acknowledging ability.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_freedom_reason:review:3:decision",
              "description": "Gives a clear release recommendation.",
              "any_of": [
                "should not be released today"
              ]
            },
            {
              "id": "wise_parrot_freedom_reason:review:3:evidence",
              "description": "Uses the wind and shelter facts while acknowledging ability.",
              "any_of": [
                "forecast strong winds",
                "lack of shelter",
                "bird can glide"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "should",
            "released",
            "today"
          ],
          "model_answer": "The kite should not be released today because the forecast strong winds and the field's lack of shelter create avoidable risk, even though the bird can glide.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_freedom_reason:review:4",
          "teaching_block": "Separate stated evidence from inference, then justify a responsible judgement with the supplied facts. Retrieve the construct, then verify it against the passage. Use the visible passage to practise inference reason and reason answer; include both details.",
          "passage": "One monkey repeatedly shakes a high branch without reaching the fruit. Another selects a fallen stick and uses it to pull the fruit closer.",
          "prompt": "Explain which action shows stronger problem solving and why.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_freedom_reason:review:4:judgement",
              "description": "Identifies the tool-using action as stronger problem solving.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_freedom_reason:review:4:reason",
              "description": "Explains the direct useful change and contrasts repetition.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_freedom_reason:review:4:judgement",
              "description": "Identifies the tool-using action as stronger problem solving.",
              "any_of": [
                "fallen stick shows stronger problem solving"
              ]
            },
            {
              "id": "wise_parrot_freedom_reason:review:4:reason",
              "description": "Explains the direct useful change and contrasts repetition.",
              "any_of": [
                "directly changes the fruit's position",
                "repeating an ineffective action"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "using",
            "fallen",
            "stick"
          ],
          "model_answer": "Using the fallen stick shows stronger problem solving because the second monkey selects a tool that directly changes the fruit's position instead of repeating an ineffective action.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "unsupported-motive-or-opinion",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "misconception": "The learner states a personal opinion as fact or invents a character motive that the text never supplies.",
          "remediation": "Label each response as stated evidence, reasonable inference, or personal judgement, then require one visible detail for every inference.",
          "support_check_ids": [
            "wise_parrot_freedom_reason:support:bridge",
            "wise_parrot_freedom_reason:support:masterclass",
            "wise_parrot_freedom_reason:support:revision_level_1",
            "wise_parrot_freedom_reason:support:revision_level_2",
            "wise_parrot_freedom_reason:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_freedom_reason:support:bridge",
          "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Break the task into one smaller decision and check it carefully.",
          "passage": "A rescued kite can hunt again and responds normally to its habitat. A trained team plans a monitored release.",
          "prompt": "Which reason best supports the plan?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "wild animals should be handled by every visitor",
            "recovery and habitat readiness support a careful release",
            "display cages are always more exciting",
            "the bird should choose a cage colour"
          ],
          "accepted_answers": [
            "recovery and habitat readiness support a careful release"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_freedom_reason:support:masterclass",
          "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Name the rule first, then apply it to this new example.",
          "passage": "A child notices a trapped butterfly and opens the window rather than trying to grab its wings.",
          "prompt": "What makes the action thoughtful?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "it reduces handling and creates a safe exit",
            "it makes the room darker",
            "it proves the child is stronger",
            "it keeps the butterfly indoors"
          ],
          "accepted_answers": [
            "it reduces handling and creates a safe exit"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_freedom_reason:support:revision_level_1",
          "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Compare the tempting error with the evidence that corrects it.",
          "passage": "A parrot asks for freedom. The story never states why the keeper first chose a golden cage.",
          "prompt": "Which answer is honest about the evidence?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "the keeper wanted to win a contest",
            "the keeper feared every forest",
            "the original motive is not stated",
            "the bird requested a gold cage"
          ],
          "accepted_answers": [
            "the original motive is not stated"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_freedom_reason:support:revision_level_2",
          "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Use the nearby context to remove an unsupported interpretation.",
          "passage": "A volunteer says, 'The owl has recovered, so a wildlife expert should decide its release.'",
          "prompt": "Which part is evidence and which is a recommendation?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "recovery is evidence; expert-guided release is the recommendation",
            "release is evidence; recovery is a guess",
            "both parts are proven motives",
            "neither part has a clear role"
          ],
          "accepted_answers": [
            "recovery is evidence; expert-guided release is the recommendation"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_freedom_reason:support:revision_level_3",
          "teaching_block": "Test each judgement against a stated action instead of guessing a hidden motive. Verify the selected answer by reading it back with the passage.",
          "passage": "A bird avoids force, communicates a plan, and waits for the right opportunity.",
          "prompt": "Which trait is most directly supported?",
          "skill_ids": [
            "reading.inference_reason"
          ],
          "options": [
            "careless",
            "strategic",
            "forgetful",
            "noisy"
          ],
          "accepted_answers": [
            "strategic"
          ]
        }
      }
    },
    {
      "level_id": "wise_parrot_words_phrases",
      "title": "Unlock words and phrases in context",
      "focus": "infer meanings and use expressions precisely",
      "outcome": "Infer a chapter word or phrase from nearby actions and use that meaning accurately in a fresh sentence.",
      "skill_ids": [
        "reading.word_meaning_context",
        "vocab.chapter_word_usage"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch04:read:1-4",
        "eng_c5_ch04:learn:6-8"
      ],
      "connect": {
        "teaching_block": "Context reveals meaning through nearby actions, feelings, positions, and results; a replacement meaning must keep the sentence sensible.",
        "passage": "Navi looked distressed when the rescued bird stopped drinking, so she called a wildlife worker at once. Her worried action explains the unfamiliar word.",
        "prompt": "Continue when you can explain how this example helps you infer meanings and use expressions precisely."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "wise_parrot_words_phrases:co_construct",
        "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Locate the exact clue before comparing the choices.",
        "passage": "Rohan was distressed when the fledgling could not stand, so he called for help.",
        "prompt": "What does distressed mean here?",
        "skill_ids": [
          "reading.word_meaning_context",
          "vocab.chapter_word_usage"
        ],
        "options": [
          "ready to celebrate",
          "worried and upset",
          "sleepy after a journey",
          "proud of a performance"
        ],
        "accepted_answers": [
          "worried and upset"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:guided:1",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Read the whole sentence, then test every option against its meaning.",
          "passage": "The myna balanced on a narrow perch above the water bowl.",
          "prompt": "What is a perch in this sentence?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "a covered nest",
            "a bird's sitting place",
            "a food container",
            "a travel cage"
          ],
          "accepted_answers": [
            "a bird's sitting place"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:guided:2",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Track who or what each detail belongs to before deciding.",
          "passage": "Mira offered to look after the injured dove until the rescuer arrived.",
          "prompt": "What does look after mean?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "care for",
            "search behind",
            "watch from far away",
            "carry outside"
          ],
          "accepted_answers": [
            "care for"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:guided:3",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "The bus was about to leave when Jatin reached the gate.",
          "prompt": "What does about to leave mean?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "had left yesterday",
            "was nearly ready to depart",
            "would never move",
            "was being repaired"
          ],
          "accepted_answers": [
            "was nearly ready to depart"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:guided:4",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Reject any option that adds a fact the passage never gives.",
          "passage": "While walking home, I came across a wet sparrow beside the path.",
          "prompt": "What does came across mean?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "painted over",
            "met or found unexpectedly",
            "walked across a bridge",
            "forgot completely"
          ],
          "accepted_answers": [
            "met or found unexpectedly"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:independent:1",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Build the answer from two visible pieces of evidence.",
          "passage": "Asha felt distressed when the nest box fell, and she immediately checked whether any chicks were inside.",
          "prompt": "Explain distressed using the action clue and use the word in a new sentence.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "meaning",
              "description": "Explains distressed as worried or upset.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "context",
              "description": "Uses the immediate checking action as the clue.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "usage",
              "description": "Uses distressed accurately in a new sentence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meaning",
              "description": "Explains distressed as worried or upset.",
              "any_of": [
                "worried",
                "upset"
              ]
            },
            {
              "id": "context",
              "description": "Uses the immediate checking action as the clue.",
              "any_of": [
                "checked immediately",
                "checked for chicks"
              ]
            },
            {
              "id": "usage",
              "description": "Uses distressed accurately in a new sentence.",
              "any_of": [
                "felt distressed",
                "was distressed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "worried",
            "upset",
            "checked",
            "immediately",
            "chicks"
          ],
          "model_answer": "Distressed means worried or upset; Asha's immediate check is the clue. I felt distressed when my pet went missing. Reference evidence states: checked immediately.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:independent:2",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. State the relationship and support it with the relevant detail.",
          "passage": "The kingfisher rested on a smooth branch that served as a perch above the pond.",
          "prompt": "Define perch from context and describe another suitable perch.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "meaning",
              "description": "Defines a perch as a raised sitting or resting place for a bird.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "example",
              "description": "Names another sensible perch.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meaning",
              "description": "Defines a perch as a raised sitting or resting place for a bird.",
              "any_of": [
                "raised sitting place",
                "place where a bird rests"
              ]
            },
            {
              "id": "example",
              "description": "Names another sensible perch.",
              "any_of": [
                "fence rail",
                "tree branch",
                "wooden bar"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 14,
          "relevance_terms": [
            "raised",
            "sitting",
            "place",
            "where",
            "bird"
          ],
          "model_answer": "A perch is a raised place where a bird sits or rests; a fence rail can also serve as a perch. Reference evidence states: raised sitting place.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:independent:3",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Explain the first part before connecting it to the result.",
          "passage": "Neel promised to look after the water bowl by cleaning and refilling it each morning.",
          "prompt": "What does look after mean here, and which two actions show it?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "meaning",
              "description": "Explains look after as care for or maintain.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "actions",
              "description": "Names cleaning and refilling.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meaning",
              "description": "Explains look after as care for or maintain.",
              "any_of": [
                "care for",
                "maintain"
              ]
            },
            {
              "id": "actions",
              "description": "Names cleaning and refilling.",
              "any_of": [
                "cleaning and refilling",
                "cleans it and fills it"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "care",
            "maintain",
            "cleaning",
            "refilling",
            "cleans"
          ],
          "model_answer": "Here, look after means care for: Neel cleans the bowl and refills it each morning. Reference evidence states: cleaning and refilling.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:independent:4",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Use your own words while preserving every required idea.",
          "passage": "The play was about to begin when the power returned.",
          "prompt": "Explain the time phrase and rewrite the idea using nearly.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "meaning",
              "description": "Explains that the play was nearly ready to begin.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "rewrite",
              "description": "Uses nearly in an accurate rewrite.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meaning",
              "description": "Explains that the play was nearly ready to begin.",
              "any_of": [
                "nearly ready to begin",
                "would begin very soon"
              ]
            },
            {
              "id": "rewrite",
              "description": "Uses nearly in an accurate rewrite.",
              "any_of": [
                "play was nearly beginning",
                "nearly time for the play"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "nearly",
            "ready",
            "begin",
            "would",
            "very"
          ],
          "model_answer": "About to begin means the play would start very soon; the play was nearly ready to begin when the power returned. Reference evidence states: play was nearly beginning.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:transfer:1",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Apply the same reasoning to a different setting and justify it.",
          "passage": "On a nature walk, the group came across a broken feeder and stopped to report it.",
          "prompt": "Infer the phrase's meaning and name the context clue.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "meaning",
              "description": "Explains came across as found unexpectedly.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "clue",
              "description": "Uses the stopping and reporting action as evidence of discovery.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meaning",
              "description": "Explains came across as found unexpectedly.",
              "any_of": [
                "found unexpectedly",
                "noticed by chance"
              ]
            },
            {
              "id": "clue",
              "description": "Uses the stopping and reporting action as evidence of discovery.",
              "any_of": [
                "stopped to report",
                "nature walk discovery"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "found",
            "unexpectedly",
            "noticed",
            "chance",
            "stopped"
          ],
          "model_answer": "Came across means found unexpectedly; stopping during the walk to report the feeder shows that the group discovered it by chance. Reference evidence states: stopped to report.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:transfer:2",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Separate what is stated from what can reasonably be inferred.",
          "passage": "When the rain ended, volunteers stepped out, checked the courtyard, and found seed scattered all over it.",
          "prompt": "Explain both stepped out and all over from the sequence.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "stepped",
              "description": "Explains stepped out as came outside.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "all_over",
              "description": "Explains all over as spread in many places.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "stepped",
              "description": "Explains stepped out as came outside.",
              "any_of": [
                "came outside",
                "left the building"
              ]
            },
            {
              "id": "all_over",
              "description": "Explains all over as spread in many places.",
              "any_of": [
                "spread in many places",
                "across the courtyard"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "came",
            "outside",
            "left",
            "building",
            "spread"
          ],
          "model_answer": "The volunteers stepped out by coming outside, and all over means the seed was spread across many parts of the courtyard. Reference evidence states: came outside; spread in many places.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:transfer:3",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Organise the response so each required point has a clear role.",
          "passage": "The caretaker went away for lunch, so another volunteer agreed to look after the recovering pigeon.",
          "prompt": "Use the cause to explain both phrases.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "went_away",
              "description": "Explains that the caretaker left the place.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "look_after",
              "description": "Explains that the volunteer took responsibility for care.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "went_away",
              "description": "Explains that the caretaker left the place.",
              "any_of": [
                "left the place",
                "was absent"
              ]
            },
            {
              "id": "look_after",
              "description": "Explains that the volunteer took responsibility for care.",
              "any_of": [
                "care for the pigeon",
                "take responsibility"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "left",
            "place",
            "absent",
            "care",
            "pigeon"
          ],
          "model_answer": "The caretaker went away by leaving for lunch, so the volunteer looked after the pigeon by taking responsibility for its care. Reference evidence states: left the place; care for the pigeon.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:transfer:4",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Use precise vocabulary instead of a vague general statement.",
          "passage": "The exhausted runner sighed, then sat quietly until her breathing slowed.",
          "prompt": "Explain sighed from the surrounding actions and use it accurately elsewhere.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "meaning",
              "description": "Explains sighed as releasing a long breath expressing feeling or tiredness.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "usage",
              "description": "Uses sighed as a verb in a sensible sentence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meaning",
              "description": "Explains sighed as releasing a long breath expressing feeling or tiredness.",
              "any_of": [
                "long breath",
                "showing tiredness"
              ]
            },
            {
              "id": "usage",
              "description": "Uses sighed as a verb in a sensible sentence.",
              "any_of": [
                "sighed with relief",
                "sighed after"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "long",
            "breath",
            "showing",
            "tiredness",
            "sighed"
          ],
          "model_answer": "Sighed means released a long breath showing tiredness; I sighed with relief when the lost keys were found.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:review:1",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Retrieve the skill after a delay and make the evidence explicit.",
          "passage": "A chick could not stand upright, but after treatment it balanced on a low perch.",
          "prompt": "Explain the two expressions and how the second event shows improvement.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "upright",
              "description": "Explains stand upright as hold a raised balanced position.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "perch",
              "description": "Explains perch as the bird's resting bar or branch.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "improvement",
              "description": "Links later balancing to recovery.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "upright",
              "description": "Explains stand upright as hold a raised balanced position.",
              "any_of": [
                "raised balanced position",
                "stand straight"
              ]
            },
            {
              "id": "perch",
              "description": "Explains perch as the bird's resting bar or branch.",
              "any_of": [
                "resting bar",
                "place to sit"
              ]
            },
            {
              "id": "improvement",
              "description": "Links later balancing to recovery.",
              "any_of": [
                "balancing shows recovery",
                "could balance later"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "raised",
            "balanced",
            "position",
            "stand",
            "straight"
          ],
          "model_answer": "Stand upright means hold a raised balanced position, and a perch is a place for a bird to sit; balancing there shows the chick improved. Reference evidence states: resting bar; balancing shows recovery.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:review:2",
          "teaching_block": "Explain the context clue, state the meaning, and use the expression in a precise new sentence. Check the final response for meaning, completeness, and support.",
          "passage": "The guide was about to close the gate when she came across a tortoise on the path.",
          "prompt": "Paraphrase both expressions without changing the event order.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "about_to",
              "description": "Paraphrases about to close as nearly ready to close.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "came_across",
              "description": "Paraphrases came across as unexpectedly found.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "about_to",
              "description": "Paraphrases about to close as nearly ready to close.",
              "any_of": [
                "nearly ready to close",
                "would close very soon"
              ]
            },
            {
              "id": "came_across",
              "description": "Paraphrases came across as unexpectedly found.",
              "any_of": [
                "unexpectedly found",
                "noticed by chance"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 14,
          "relevance_terms": [
            "nearly",
            "ready",
            "close",
            "would",
            "very"
          ],
          "model_answer": "The guide was nearly ready to close the gate when she unexpectedly found a tortoise on the path.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "about_to",
            "came_across"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:review:3",
          "teaching_block": "Use nearby actions and results to infer meaning, then place the expression in a precise new sentence. Retrieve the construct, then verify it against the passage. Use the visible passage to practise word meaning context and chapter word usage; include both details.",
          "passage": "Mina hesitated at the rope bridge: she paused, tested the first plank, and looked back before stepping forward.",
          "prompt": "Infer hesitated from the actions, then use the word in a fresh sentence about a careful choice.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_words_phrases:review:3:meaning",
              "description": "Defines hesitated from Mina's pause and uncertainty.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_words_phrases:review:3:usage",
              "description": "Uses hesitated accurately in a new careful-choice sentence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_words_phrases:review:3:meaning",
              "description": "Defines hesitated from Mina's pause and uncertainty.",
              "any_of": [
                "means paused",
                "Mina was uncertain"
              ]
            },
            {
              "id": "wise_parrot_words_phrases:review:3:usage",
              "description": "Uses hesitated accurately in a new careful-choice sentence.",
              "any_of": [
                "Arav hesitated before choosing",
                "loose stones"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "hesitated",
            "means",
            "paused"
          ],
          "model_answer": "Hesitated means paused because Mina was uncertain. In a new sentence: Arav hesitated before choosing the steeper path because loose stones covered it.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_words_phrases:review:4",
          "teaching_block": "Use nearby actions and results to infer meaning, then place the expression in a precise new sentence. Retrieve the construct, then verify it against the passage. Use the visible passage to practise word meaning context and chapter word usage; include both details.",
          "passage": "The ranger set the recovered deer free. It bounded through the open gate and disappeared among the trees.",
          "prompt": "Explain set free from the result clue and use the phrase in another accurate sentence.",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_words_phrases:review:4:context",
              "description": "Explains the phrase using the open-gate result.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_words_phrases:review:4:new_use",
              "description": "Uses set free accurately in a new sentence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_words_phrases:review:4:context",
              "description": "Explains the phrase using the open-gate result.",
              "any_of": [
                "means released from control",
                "running through the open gate"
              ]
            },
            {
              "id": "wise_parrot_words_phrases:review:4:new_use",
              "description": "Uses set free accurately in a new sentence.",
              "any_of": [
                "set the healed kite free",
                "safe grassland habitat"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "means",
            "released",
            "control"
          ],
          "model_answer": "Set free means released from control, shown by the deer running through the open gate. The volunteers set the healed kite free beside its safe grassland habitat.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "context-replaced-by-guess",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "misconception": "The learner chooses a familiar dictionary meaning without checking whether nearby actions and results support it.",
          "remediation": "Underline the action clue, replace the target expression with a candidate meaning, and reread the full sentence for sense.",
          "support_check_ids": [
            "wise_parrot_words_phrases:support:bridge",
            "wise_parrot_words_phrases:support:masterclass",
            "wise_parrot_words_phrases:support:revision_level_1",
            "wise_parrot_words_phrases:support:revision_level_2",
            "wise_parrot_words_phrases:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:support:bridge",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Break the task into one smaller decision and check it carefully.",
          "passage": "The puppy could not stand upright after slipping, so Tara supported it gently.",
          "prompt": "What does stand upright mean?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "lie under a chair",
            "remain hidden",
            "stand in a straight raised position",
            "move in a circle"
          ],
          "accepted_answers": [
            "stand in a straight raised position"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:support:masterclass",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Name the rule first, then apply it to this new example.",
          "passage": "After the storm, leaves were scattered all over the courtyard.",
          "prompt": "What does all over describe?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "in many parts of the place",
            "under one single tile",
            "only beyond the gate",
            "inside a closed box"
          ],
          "accepted_answers": [
            "in many parts of the place"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:support:revision_level_1",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Compare the tempting error with the evidence that corrects it.",
          "passage": "The caretaker stepped out of the office to inspect the feeder.",
          "prompt": "What does stepped out mean?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "left or came outside briefly",
            "jumped over a step",
            "sat at the desk",
            "closed every window"
          ],
          "accepted_answers": [
            "left or came outside briefly"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:support:revision_level_2",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Use the nearby context to remove an unsupported interpretation.",
          "passage": "The flock went away when the loud machine started.",
          "prompt": "What does went away mean?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "moved to another place",
            "grew louder",
            "returned immediately",
            "built a nest"
          ],
          "accepted_answers": [
            "moved to another place"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_words_phrases:support:revision_level_3",
          "teaching_block": "Substitute a possible meaning and check whether the surrounding action still makes sense. Verify the selected answer by reading it back with the passage.",
          "passage": "The bird sighed after the window was closed again.",
          "prompt": "Which meaning best fits sighed?",
          "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "made a long breath showing feeling",
            "sang a victory song",
            "flapped in a race",
            "ate very quickly"
          ],
          "accepted_answers": [
            "made a long breath showing feeling"
          ]
        }
      }
    },
    {
      "level_id": "wise_parrot_collective_nouns",
      "title": "Name groups precisely",
      "focus": "select and use conventional collective nouns",
      "outcome": "Choose an appropriate collective noun for a familiar group and use it in a complete meaningful sentence.",
      "skill_ids": [
        "grammar.noun_verb_adjective",
        "vocab.chapter_word_usage"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch04:learn:6-8"
      ],
      "connect": {
        "teaching_block": "A collective noun names many members as one group, but the noun must match the people, animals, or objects being grouped.",
        "passage": "A flock of sheep crossed the field, while a swarm of bees circled the flowers. The group words are not interchangeable.",
        "prompt": "Continue when you can explain how this example helps you select and use conventional collective nouns."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "wise_parrot_collective_nouns:co_construct",
        "teaching_block": "Match the conventional group word to the noun before completing the sentence. Locate the exact clue before comparing the choices.",
        "passage": "A ___ of parrots crossed the evening sky.",
        "prompt": "Which group word fits?",
        "skill_ids": [
          "grammar.noun_verb_adjective",
          "vocab.chapter_word_usage"
        ],
        "options": [
          "bouquet",
          "flight",
          "army",
          "bunch"
        ],
        "accepted_answers": [
          "flight"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:guided:1",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Read the whole sentence, then test every option against its meaning.",
          "passage": "A ___ of sheep followed the farmer.",
          "prompt": "Which collective noun completes the sentence?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "swarm",
            "pack",
            "flock",
            "flight"
          ],
          "accepted_answers": [
            "flock"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:guided:2",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Track who or what each detail belongs to before deciding.",
          "passage": "A ___ of wolves moved through the snow.",
          "prompt": "Which word names this group?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "pack",
            "bouquet",
            "army",
            "bunch"
          ],
          "accepted_answers": [
            "pack"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:guided:3",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "The guest received a ___ of flowers.",
          "prompt": "Which group noun is conventional?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "flock",
            "bouquet",
            "swarm",
            "flight"
          ],
          "accepted_answers": [
            "bouquet"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:guided:4",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Reject any option that adds a fact the passage never gives.",
          "passage": "A ___ of bees gathered near the hive.",
          "prompt": "Which collective noun fits?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "bunch",
            "army",
            "swarm",
            "pack"
          ],
          "accepted_answers": [
            "swarm"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:independent:1",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Build the answer from two visible pieces of evidence.",
          "passage": "Several parrots rise together from one tree at sunset.",
          "prompt": "Name the group and write a complete sentence about its movement.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "group",
              "description": "Uses flight as the group word for parrots moving together.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "sentence",
              "description": "Writes a complete sentence with a clear action.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "group",
              "description": "Uses flight as the group word for parrots moving together.",
              "any_of": [
                "flight of parrots"
              ]
            },
            {
              "id": "sentence",
              "description": "Writes a complete sentence with a clear action.",
              "any_of": [
                "flight of parrots rose",
                "flight crossed the sky"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "flight",
            "parrots",
            "rose",
            "crossed"
          ],
          "model_answer": "A flight of parrots rose together from the tree and crossed the sunset sky.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:independent:2",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. State the relationship and support it with the relevant detail.",
          "passage": "Many bees leave a hive and gather around one flowering bush.",
          "prompt": "Choose the precise group noun and explain why flock would not fit.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "swarm",
              "description": "Uses swarm for the bees.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "contrast",
              "description": "Explains that flock is conventionally used for birds or sheep, not bees.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "swarm",
              "description": "Uses swarm for the bees.",
              "any_of": [
                "swarm of bees"
              ]
            },
            {
              "id": "contrast",
              "description": "Explains that flock is conventionally used for birds or sheep, not bees.",
              "any_of": [
                "flock is for birds",
                "flock does not fit bees"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "swarm",
            "bees",
            "flock",
            "birds",
            "does"
          ],
          "model_answer": "A swarm of bees gathered around the bush; flock would not fit because it is conventionally used for birds or sheep. Reference evidence states: flock is for birds.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:independent:3",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Explain the first part before connecting it to the result.",
          "passage": "Seven keys are tied together with one metal ring.",
          "prompt": "Use the conventional group expression in a complete sentence.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "bunch",
              "description": "Uses bunch of keys.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "complete",
              "description": "Includes a subject and complete action or state.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "bunch",
              "description": "Uses bunch of keys.",
              "any_of": [
                "bunch of keys"
              ]
            },
            {
              "id": "complete",
              "description": "Includes a subject and complete action or state.",
              "any_of": [
                "bunch of keys was",
                "found a bunch"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 9,
          "relevance_terms": [
            "bunch",
            "keys",
            "found"
          ],
          "model_answer": "A bunch of keys was hanging from the hook beside the office door.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:independent:4",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Use your own words while preserving every required idea.",
          "passage": "A guest receives roses, marigolds, and leaves arranged together.",
          "prompt": "Name the arranged group and describe it in one complete sentence.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "bouquet",
              "description": "Uses bouquet of flowers.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "description",
              "description": "Adds an accurate descriptive or action detail.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "bouquet",
              "description": "Uses bouquet of flowers.",
              "any_of": [
                "bouquet of flowers",
                "flower bouquet"
              ]
            },
            {
              "id": "description",
              "description": "Adds an accurate descriptive or action detail.",
              "any_of": [
                "colourful bouquet",
                "was presented"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "bouquet",
            "flowers",
            "flower",
            "colourful",
            "presented"
          ],
          "model_answer": "The guest received a colourful bouquet of flowers at the end of the programme.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:transfer:1",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Apply the same reasoning to a different setting and justify it.",
          "passage": "A wildlife note mentions wolves moving and hunting together.",
          "prompt": "Write a sentence using the precise collective noun and one action.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "pack",
              "description": "Uses pack of wolves.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Includes a sensible group action.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "pack",
              "description": "Uses pack of wolves.",
              "any_of": [
                "pack of wolves"
              ]
            },
            {
              "id": "action",
              "description": "Includes a sensible group action.",
              "any_of": [
                "moved together",
                "tracked through",
                "hunted"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "pack",
            "wolves",
            "moved",
            "together",
            "tracked"
          ],
          "model_answer": "A pack of wolves moved together along the snowy edge of the forest.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:transfer:2",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Separate what is stated from what can reasonably be inferred.",
          "passage": "Ants carry crumbs along the same narrow trail.",
          "prompt": "Use army accurately and explain what the group word adds.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "army",
              "description": "Uses army of ants in a complete sentence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "group_meaning",
              "description": "Explains that the word treats many ants as one organised group.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "army",
              "description": "Uses army of ants in a complete sentence.",
              "any_of": [
                "army of ants"
              ]
            },
            {
              "id": "group_meaning",
              "description": "Explains that the word treats many ants as one organised group.",
              "any_of": [
                "organised group",
                "many ants together"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "army",
            "ants",
            "organised",
            "group",
            "many"
          ],
          "model_answer": "An army of ants carried crumbs along the trail; the group word presents the many ants as one organised unit. Reference evidence states: organised group.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:transfer:3",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Organise the response so each required point has a clear role.",
          "passage": "Maps from different states are arranged for a geography display.",
          "prompt": "Use collection in a complete sentence and state what is grouped.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "collection",
              "description": "Uses collection of maps.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "members",
              "description": "Identifies maps from different states as the grouped members.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "collection",
              "description": "Uses collection of maps.",
              "any_of": [
                "collection of maps"
              ]
            },
            {
              "id": "members",
              "description": "Identifies maps from different states as the grouped members.",
              "any_of": [
                "maps from different states",
                "state maps"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 11,
          "relevance_terms": [
            "collection",
            "maps",
            "from",
            "different",
            "states"
          ],
          "model_answer": "The class displayed a collection of maps from different states on one wall.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:transfer:4",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Use precise vocabulary instead of a vague general statement.",
          "passage": "Performers rehearse a dance together before entering the stage.",
          "prompt": "Use troupe in a sentence that makes the meaning clear.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "troupe",
              "description": "Uses troupe of dancers or dance troupe.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "context",
              "description": "Includes rehearsal or performance context.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "troupe",
              "description": "Uses troupe of dancers or dance troupe.",
              "any_of": [
                "troupe of dancers",
                "dance troupe"
              ]
            },
            {
              "id": "context",
              "description": "Includes rehearsal or performance context.",
              "any_of": [
                "rehearsed",
                "performed",
                "entered the stage"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "troupe",
            "dancers",
            "dance",
            "rehearsed",
            "performed"
          ],
          "model_answer": "The dance troupe rehearsed together before entering the stage for its performance.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:review:1",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Retrieve the skill after a delay and make the evidence explicit.",
          "passage": "Sheep and bees are both moving in groups near a farm.",
          "prompt": "Write two sentences using the correct different group nouns.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "flock",
              "description": "Uses flock of sheep.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "swarm",
              "description": "Uses swarm of bees.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "flock",
              "description": "Uses flock of sheep.",
              "any_of": [
                "flock of sheep"
              ]
            },
            {
              "id": "swarm",
              "description": "Uses swarm of bees.",
              "any_of": [
                "swarm of bees"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "flock",
            "sheep",
            "swarm",
            "bees"
          ],
          "model_answer": "A flock of sheep crossed the field. A swarm of bees circled the nearby flowers.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:review:2",
          "teaching_block": "Name the group precisely and use the collective noun in a complete context that proves its meaning. Check the final response for meaning, completeness, and support.",
          "passage": "Parrots fly overhead, wolves travel through trees, and flowers are arranged for a visitor.",
          "prompt": "Use three different collective nouns without swapping them.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "flight",
              "description": "Uses flight for parrots.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "pack",
              "description": "Uses pack for wolves.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "bouquet",
              "description": "Uses bouquet for flowers.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "flight",
              "description": "Uses flight for parrots.",
              "any_of": [
                "flight of parrots"
              ]
            },
            {
              "id": "pack",
              "description": "Uses pack for wolves.",
              "any_of": [
                "pack of wolves"
              ]
            },
            {
              "id": "bouquet",
              "description": "Uses bouquet for flowers.",
              "any_of": [
                "bouquet of flowers"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 16,
          "relevance_terms": [
            "flight",
            "parrots",
            "pack",
            "wolves",
            "bouquet"
          ],
          "model_answer": "A flight of parrots crossed above a pack of wolves, while the visitor carried a bouquet of flowers.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:review:3",
          "teaching_block": "Choose a group noun that fits the members, then check the job of each key word in the sentence. Retrieve the construct, then verify it against the passage. Use the visible passage to practise noun verb adjective and chapter word usage; include both details.",
          "passage": "Six musicians perform a lively tune together on the school stage.",
          "prompt": "Write a sentence using band, then classify band, perform, and lively by their jobs.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_collective_nouns:review:3:group",
              "description": "Uses band as the collective noun in a complete sentence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_collective_nouns:review:3:jobs",
              "description": "Classifies the noun, verb, and adjective by function.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_collective_nouns:review:3:group",
              "description": "Uses band as the collective noun in a complete sentence.",
              "any_of": [
                "A band of musicians"
              ]
            },
            {
              "id": "wise_parrot_collective_nouns:review:3:jobs",
              "description": "Classifies the noun, verb, and adjective by function.",
              "any_of": [
                "Band is a noun",
                "performs is a verb",
                "lively is an adjective"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "musicians",
            "performs",
            "lively"
          ],
          "model_answer": "A band of musicians performs a lively tune. Band is a noun naming the group, performs is a verb naming the action, and lively is an adjective describing the tune.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_collective_nouns:review:4",
          "teaching_block": "Choose a group noun that fits the members, then check the job of each key word in the sentence. Retrieve the construct, then verify it against the passage. Use the visible passage to practise noun verb adjective and chapter word usage; include both details.",
          "passage": "Several boats move quietly into the harbour while a bright signal flashes above them.",
          "prompt": "Use fleet for the group and identify the verb and adjective in your completed sentence.",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_collective_nouns:review:4:fleet",
              "description": "Uses fleet for the group of boats.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_collective_nouns:review:4:grammar",
              "description": "Identifies the action verb and describing adjective.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_collective_nouns:review:4:fleet",
              "description": "Uses fleet for the group of boats.",
              "any_of": [
                "A fleet of boats"
              ]
            },
            {
              "id": "wise_parrot_collective_nouns:review:4:grammar",
              "description": "Identifies the action verb and describing adjective.",
              "any_of": [
                "enters is the verb",
                "bright is the adjective"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "fleet",
            "boats",
            "enters"
          ],
          "model_answer": "A fleet of boats enters the harbour quietly under a bright signal. Fleet is the group noun, enters is the verb, and bright is the adjective describing the signal.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "collective-noun-interchange",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "misconception": "The learner treats every group noun as interchangeable or selects one only because it sounds familiar.",
          "remediation": "Pair each collective noun with its conventional member noun, then verify it inside a complete sentence before moving on.",
          "support_check_ids": [
            "wise_parrot_collective_nouns:support:bridge",
            "wise_parrot_collective_nouns:support:masterclass",
            "wise_parrot_collective_nouns:support:revision_level_1",
            "wise_parrot_collective_nouns:support:revision_level_2",
            "wise_parrot_collective_nouns:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:support:bridge",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Break the task into one smaller decision and check it carefully.",
          "passage": "An ___ of ants crossed the path.",
          "prompt": "Which group noun is expected?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "army",
            "bouquet",
            "flight",
            "flock"
          ],
          "accepted_answers": [
            "army"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:support:masterclass",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Name the rule first, then apply it to this new example.",
          "passage": "Mira found a ___ of keys in the drawer.",
          "prompt": "Which word names the group?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "pack",
            "bunch",
            "swarm",
            "flock"
          ],
          "accepted_answers": [
            "bunch"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:support:revision_level_1",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Compare the tempting error with the evidence that corrects it.",
          "passage": "A ___ of fish turned together near the reef.",
          "prompt": "Which familiar collective noun fits?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "school",
            "bouquet",
            "army",
            "flight"
          ],
          "accepted_answers": [
            "school"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:support:revision_level_2",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Use the nearby context to remove an unsupported interpretation.",
          "passage": "The library displayed a ___ of maps prepared for the project.",
          "prompt": "Which general group noun fits best?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "collection",
            "swarm",
            "flock",
            "pack"
          ],
          "accepted_answers": [
            "collection"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_collective_nouns:support:revision_level_3",
          "teaching_block": "Match the conventional group word to the noun before completing the sentence. Verify the selected answer by reading it back with the passage.",
          "passage": "A ___ of dancers entered in one organised line.",
          "prompt": "Which word can name the performing group?",
          "skill_ids": [
            "grammar.noun_verb_adjective",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "troupe",
            "flight",
            "bunch",
            "swarm"
          ],
          "accepted_answers": [
            "troupe"
          ]
        }
      }
    },
    {
      "level_id": "wise_parrot_present_perfect",
      "title": "Connect completed actions to now",
      "focus": "form and use the present perfect accurately",
      "outcome": "Choose has or have for the subject and combine it with a correct past participle in a meaningful complete sentence.",
      "skill_ids": [
        "grammar.tense_usage",
        "writing.complete_sentence"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch04:learn:6-8"
      ],
      "connect": {
        "teaching_block": "The present perfect uses has or have plus a past participle for a completed action that matters now or an experience before now.",
        "passage": "Mira has cleaned the water bowl, so it is ready for the birds now. The completed action has a present result.",
        "prompt": "Continue when you can explain how this example helps you form and use the present perfect accurately."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "wise_parrot_present_perfect:co_construct",
        "teaching_block": "Match the auxiliary to the subject and check the past-participle form before selecting. Locate the exact clue before comparing the choices.",
        "passage": "Riya ___ visited the sanctuary twice.",
        "prompt": "Which auxiliary completes the sentence?",
        "skill_ids": [
          "grammar.tense_usage"
        ],
        "options": [
          "have",
          "has",
          "is",
          "did"
        ],
        "accepted_answers": [
          "has"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_present_perfect:guided:1",
          "teaching_block": "Match the auxiliary to the subject and check the past-participle form before selecting. Read the whole sentence, then test every option against its meaning.",
          "passage": "The volunteers ___ filled every water bowl.",
          "prompt": "Which word agrees with the plural subject?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "has",
            "is",
            "have",
            "was"
          ],
          "accepted_answers": [
            "have"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:guided:2",
          "teaching_block": "Write a complete present-perfect sentence and connect the completed action to its present relevance. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "Nila finished the observation chart, and it is ready to submit.",
          "prompt": "Write one complete present-perfect sentence with the correct auxiliary and participle.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "verb_phrase",
              "description": "Uses has completed or has finished.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "complete",
              "description": "Includes Nila and the chart in a complete sentence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "verb_phrase",
              "description": "Uses has completed or has finished.",
              "any_of": [
                "has completed",
                "has finished"
              ]
            },
            {
              "id": "complete",
              "description": "Includes Nila and the chart in a complete sentence.",
              "any_of": [
                "Nila has",
                "observation chart"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "completed",
            "finished",
            "nila",
            "observation",
            "chart"
          ],
          "model_answer": "Nila has completed the observation chart, so it is ready to submit.",
          "pass_score": 0.8
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_present_perfect:guided:3",
          "teaching_block": "Look for a finished action whose result matters now, then select has or have plus the past participle.",
          "passage": "The keeper cleaned the water tray ten minutes ago. It is ready for the birds now.",
          "prompt": "Which sentence links the completed action to the present result?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "The keeper has cleaned the water tray.",
            "The keeper clean the water tray tomorrow.",
            "The keeper was cleaning every tray next week.",
            "The keeper had clean the tray now."
          ],
          "accepted_answers": [
            "The keeper has cleaned the water tray."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_present_perfect:guided:4",
          "teaching_block": "Match the plural subject with have and use the past-participle form of the main verb.",
          "passage": "Two volunteers repaired the loose perches this morning, so the enclosure is safe now.",
          "prompt": "Which sentence reports the useful present result correctly?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "The volunteers has repaired the loose perches.",
            "The volunteers have repaired the loose perches.",
            "The volunteers have repair the loose perches.",
            "The volunteers repairs the loose perches yesterday."
          ],
          "accepted_answers": [
            "The volunteers have repaired the loose perches."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:independent:1",
          "teaching_block": "Write a complete present-perfect sentence and connect the completed action to its present relevance. Build the answer from two visible pieces of evidence.",
          "passage": "Ravi finished cleaning the feeder, and it is ready for fresh seed now.",
          "prompt": "Write one present-perfect sentence joining the completed action to the present result.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "form",
              "description": "Uses has or have plus a correct past participle.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "complete",
              "description": "Forms a complete meaningful sentence about the feeder.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "form",
              "description": "Uses has or have plus a correct past participle.",
              "any_of": [
                "has cleaned",
                "has finished cleaning"
              ]
            },
            {
              "id": "complete",
              "description": "Forms a complete meaningful sentence about the feeder.",
              "any_of": [
                "feeder is ready",
                "Ravi has cleaned the feeder"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "cleaned",
            "finished",
            "cleaning",
            "feeder",
            "ready"
          ],
          "model_answer": "Ravi has cleaned the feeder, so it is ready for fresh seed now.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:independent:2",
          "teaching_block": "Write a complete present-perfect sentence and connect the completed action to its present relevance. State the relationship and support it with the relevant detail.",
          "passage": "The class visited two bird habitats before today's discussion.",
          "prompt": "Write a complete sentence about this experience using the present perfect.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "form",
              "description": "Uses have visited with the plural subject.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "experience",
              "description": "Connects the visits to experience before now.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "form",
              "description": "Uses have visited with the plural subject.",
              "any_of": [
                "class has visited",
                "students have visited"
              ]
            },
            {
              "id": "experience",
              "description": "Connects the visits to experience before now.",
              "any_of": [
                "visited two habitats",
                "before today's discussion"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "class",
            "visited",
            "students",
            "have",
            "habitats"
          ],
          "model_answer": "The class has visited two bird habitats before today's discussion.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:independent:3",
          "teaching_block": "Build the first sentence with has plus the past participle, then state the visible result in a separate complete sentence.",
          "passage": "Today the rescue team fitted a soft cover over the recovery cage. The recovering bird is protected from harsh sunlight now.",
          "prompt": "Write one present-perfect sentence about the action and one sentence about its present result.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "short_text",
          "rubric_criteria": [
            {
              "id": "form",
              "description": "Uses has fitted for the completed action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "States the protection that exists now.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "form",
              "description": "Uses has fitted for the completed action.",
              "any_of": [
                "has fitted a soft cover"
              ]
            },
            {
              "id": "result",
              "description": "States the protection that exists now.",
              "any_of": [
                "now protected from harsh sunlight"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 14,
          "relevance_terms": [
            "today",
            "rescue",
            "team",
            "fitted",
            "soft",
            "cover",
            "over",
            "recovery"
          ],
          "model_answer": "The rescue team has fitted a soft cover over the recovery cage. The bird is now protected from harsh sunlight.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:independent:4",
          "teaching_block": "Use simple past with last Saturday, but use present perfect when the completed work explains today's situation.",
          "passage": "Last Saturday, Nila labelled three feed jars. Today, every helper can choose the correct food quickly.",
          "prompt": "Write one simple-past sentence for the finished time and one present-perfect sentence linking the work to today.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "short_text",
          "rubric_criteria": [
            {
              "id": "past",
              "description": "Uses simple past with the stated finished time.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "present_link",
              "description": "Uses present perfect for the result that matters today.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "past",
              "description": "Uses simple past with the stated finished time.",
              "any_of": [
                "labelled three feed jars last Saturday"
              ]
            },
            {
              "id": "present_link",
              "description": "Uses present perfect for the result that matters today.",
              "any_of": [
                "has made food selection quicker"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "last",
            "saturday",
            "nila",
            "labelled",
            "three",
            "feed",
            "jars",
            "today"
          ],
          "model_answer": "Nila labelled three feed jars last Saturday. She has made food selection quicker for every helper today.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "past",
            "present_link"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:transfer:1",
          "teaching_block": "Write a complete present-perfect sentence and connect the completed action to its present relevance. Explain the first part before connecting it to the result.",
          "passage": "Leena finished three sketches, and all three are displayed now.",
          "prompt": "Express the completed work and its present relevance in one sentence.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "tense",
              "description": "Uses has drawn or has completed.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Mentions that the sketches are displayed now.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "tense",
              "description": "Uses has drawn or has completed.",
              "any_of": [
                "has drawn",
                "has completed"
              ]
            },
            {
              "id": "result",
              "description": "Mentions that the sketches are displayed now.",
              "any_of": [
                "displayed now",
                "are on display"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 9,
          "relevance_terms": [
            "drawn",
            "completed",
            "displayed",
            "display"
          ],
          "model_answer": "Leena has drawn three sketches, and they are displayed now.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:transfer:2",
          "teaching_block": "Write a complete present-perfect sentence and connect the completed action to its present relevance. Use your own words while preserving every required idea.",
          "passage": "The rescue team chose a safe release site before making today's plan.",
          "prompt": "Write the idea with a correct present-perfect verb phrase.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "chosen",
              "description": "Uses has chosen with the singular team.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "site",
              "description": "Names the safe release site and present plan.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "chosen",
              "description": "Uses has chosen with the singular team.",
              "any_of": [
                "team has chosen",
                "has selected"
              ]
            },
            {
              "id": "site",
              "description": "Names the safe release site and present plan.",
              "any_of": [
                "safe release site",
                "today's plan"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 9,
          "relevance_terms": [
            "team",
            "chosen",
            "selected",
            "safe",
            "release"
          ],
          "model_answer": "The rescue team has chosen a safe release site for today's plan.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:transfer:3",
          "teaching_block": "Transfer the tense rule to a new setting and support it with the current result supplied in the passage.",
          "passage": "A reading club began recording local bird sightings on Monday. Its chart now contains twenty verified entries.",
          "prompt": "Use the present perfect to connect the club's work with the chart that exists now, then state the evidence.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "form",
              "description": "Uses has recorded to connect past work with now.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Uses the twenty verified entries as current evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "form",
              "description": "Uses has recorded to connect past work with now.",
              "any_of": [
                "has recorded local bird sightings"
              ]
            },
            {
              "id": "evidence",
              "description": "Uses the twenty verified entries as current evidence.",
              "any_of": [
                "chart now contains twenty verified entries"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 16,
          "relevance_terms": [
            "reading",
            "club",
            "began",
            "recording",
            "local",
            "bird",
            "sightings",
            "monday"
          ],
          "model_answer": "The reading club has recorded local bird sightings since Monday. Its chart now contains twenty verified entries as evidence of that work.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:transfer:4",
          "teaching_block": "Match has or have to the subject and use the past participle to connect completed work with a present result. Apply the same construct to this new passage. Use the visible passage to practise tense usage and complete sentence; include both details.",
          "passage": "The gardeners planted six native saplings this week, and all six now stand beside the pond.",
          "prompt": "Connect the completed planting with the present pond view in one correct sentence.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_present_perfect:transfer:4:verb",
              "description": "Uses have with the correct past participle.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_present_perfect:transfer:4:result",
              "description": "States the present visible result in a complete sentence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_present_perfect:transfer:4:verb",
              "description": "Uses have with the correct past participle.",
              "any_of": [
                "gardeners have planted"
              ]
            },
            {
              "id": "wise_parrot_present_perfect:transfer:4:result",
              "description": "States the present visible result in a complete sentence.",
              "any_of": [
                "all six now stand beside the pond"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "gardeners",
            "planted",
            "native"
          ],
          "model_answer": "The gardeners have planted six native saplings, and all six now stand beside the pond.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:review:1",
          "teaching_block": "Write a complete present-perfect sentence and connect the completed action to its present relevance. Apply the same reasoning to a different setting and justify it.",
          "passage": "You completed your bird-fact card, and your partner can read it now.",
          "prompt": "Retrieve the present perfect and write the full result sentence.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "completed",
              "description": "Uses have completed with you.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "States that the partner can read it now.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "completed",
              "description": "Uses have completed with you.",
              "any_of": [
                "you have completed",
                "you have finished"
              ]
            },
            {
              "id": "result",
              "description": "States that the partner can read it now.",
              "any_of": [
                "partner can read",
                "ready to read"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "have",
            "completed",
            "finished",
            "partner",
            "read"
          ],
          "model_answer": "You have completed the bird-fact card, so your partner can read it now.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:review:2",
          "teaching_block": "Write a complete present-perfect sentence and connect the completed action to its present relevance. Separate what is stated from what can reasonably be inferred.",
          "passage": "Two volunteers refilled the bowls, and no bowl is empty now.",
          "prompt": "Use the correct auxiliary and participle in a complete sentence.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "plural_form",
              "description": "Uses have refilled for the plural subject.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "present_result",
              "description": "Connects the action to no bowl being empty.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "plural_form",
              "description": "Uses have refilled for the plural subject.",
              "any_of": [
                "volunteers have refilled",
                "they have filled"
              ]
            },
            {
              "id": "present_result",
              "description": "Connects the action to no bowl being empty.",
              "any_of": [
                "no bowl is empty",
                "bowls are full now"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "volunteers",
            "have",
            "refilled",
            "they",
            "filled"
          ],
          "model_answer": "The volunteers have refilled the bowls, so no bowl is empty now.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:review:3",
          "teaching_block": "Match has or have to the subject and use the past participle to connect completed work with a present result. Retrieve the construct, then verify it against the passage. Use the visible passage to practise tense usage and complete sentence; include both details.",
          "passage": "Rohan completed a guide to four local birds, and the guide is ready for today's display.",
          "prompt": "Use the present perfect to join Rohan's finished work with its current result.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_present_perfect:review:3:tense",
              "description": "Uses has completed for the singular subject.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_present_perfect:review:3:present",
              "description": "Connects the completed work with today's readiness.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_present_perfect:review:3:tense",
              "description": "Uses has completed for the singular subject.",
              "any_of": [
                "Rohan has completed"
              ]
            },
            {
              "id": "wise_parrot_present_perfect:review:3:present",
              "description": "Connects the completed work with today's readiness.",
              "any_of": [
                "ready for today's display"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "rohan",
            "completed",
            "guide"
          ],
          "model_answer": "Rohan has completed a guide to four local birds, and it is ready for today's display.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_present_perfect:review:4",
          "teaching_block": "Match has or have to the subject and use the past participle to connect completed work with a present result. Retrieve the construct, then verify it against the passage. Use the visible passage to practise tense usage and complete sentence; include both details.",
          "passage": "Two swallows built nests under the roof, and both nests remain visible above the veranda.",
          "prompt": "Write a complete present-perfect sentence that preserves the plural subject and present result.",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_present_perfect:review:4:form",
              "description": "Uses have built with the plural subject.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_present_perfect:review:4:result",
              "description": "Includes the present location and visibility.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_present_perfect:review:4:form",
              "description": "Uses have built with the plural subject.",
              "any_of": [
                "swallows have built"
              ]
            },
            {
              "id": "wise_parrot_present_perfect:review:4:result",
              "description": "Includes the present location and visibility.",
              "any_of": [
                "remain visible above the veranda"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "swallows",
            "built",
            "nests"
          ],
          "model_answer": "The two swallows have built nests under the roof, and both nests remain visible above the veranda.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "auxiliary-or-participle-error",
          "skill_ids": [
            "grammar.tense_usage",
            "writing.complete_sentence"
          ],
          "misconception": "The learner chooses has or have without checking the subject, or places a base/simple-past verb after the auxiliary.",
          "remediation": "Mark the subject as singular or plural, choose has or have, then verify the irregular or regular past participle separately.",
          "support_check_ids": [
            "wise_parrot_present_perfect:support:bridge",
            "wise_parrot_present_perfect:support:masterclass",
            "wise_parrot_present_perfect:support:revision_level_1",
            "wise_parrot_present_perfect:support:revision_level_2",
            "wise_parrot_present_perfect:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_present_perfect:support:bridge",
          "teaching_block": "Match the auxiliary to the subject and check the past-participle form before selecting. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "I have ___ my observation notes.",
          "prompt": "Which verb form is correct?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "wrote",
            "written",
            "write",
            "writing"
          ],
          "accepted_answers": [
            "written"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_present_perfect:support:masterclass",
          "teaching_block": "Match the auxiliary to the subject and check the past-participle form before selecting. Reject any option that adds a fact the passage never gives.",
          "passage": "The chick has ___ enough to return outdoors.",
          "prompt": "Which completed form fits?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "recover",
            "recovered",
            "recovering",
            "recovers"
          ],
          "accepted_answers": [
            "recovered"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_present_perfect:support:revision_level_1",
          "teaching_block": "Match the auxiliary to the subject and check the past-participle form before selecting. Break the task into one smaller decision and check it carefully.",
          "passage": "My friends ___ completed the bird chart.",
          "prompt": "Which auxiliary fits the subject?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "has",
            "have",
            "was",
            "does"
          ],
          "accepted_answers": [
            "have"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_present_perfect:support:revision_level_2",
          "teaching_block": "Match the auxiliary to the subject and check the past-participle form before selecting. Name the rule first, then apply it to this new example.",
          "passage": "Asha has ___ three careful sketches.",
          "prompt": "Which form completes the present perfect?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "draw",
            "drew",
            "drawn",
            "drawing"
          ],
          "accepted_answers": [
            "drawn"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_present_perfect:support:revision_level_3",
          "teaching_block": "Match the auxiliary to the subject and check the past-participle form before selecting. Compare the tempting error with the evidence that corrects it.",
          "passage": "We have ___ the safe location already.",
          "prompt": "Which past participle is correct?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "choose",
            "chose",
            "chosen",
            "choosing"
          ],
          "accepted_answers": [
            "chosen"
          ]
        }
      }
    },
    {
      "level_id": "wise_parrot_bird_sanctuary",
      "title": "Select and report bird facts",
      "focus": "find main ideas and choose relevant information",
      "outcome": "Select relevant facts from a bounded bird-information packet and summarise its main idea without inventing unsupported details.",
      "skill_ids": [
        "reading.paragraph_main_idea",
        "writing.summary_own_words",
        "research.information_selection"
      ],
      "episode_kind": "retrieval_challenge",
      "source_anchor_ids": [
        "eng_c5_ch04:explore:12"
      ],
      "connect": {
        "teaching_block": "A reliable fact report begins with the source packet's central idea, then selects only details that answer the stated question.",
        "passage": "Fact packet: A wetland reserve protects nesting islands and limits boats during breeding months. Both details support the main idea of reducing disturbance.",
        "prompt": "Continue when you can explain how this example helps you find main ideas and choose relevant information."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "wise_parrot_bird_sanctuary:co_construct",
        "teaching_block": "Choose the detail that answers the research question and belongs to the supplied packet. Locate the exact clue before comparing the choices.",
        "passage": "Packet: The reserve keeps a shallow pool and protects reed beds where birds shelter.",
        "prompt": "Which main idea joins both details?",
        "skill_ids": [
          "reading.paragraph_main_idea",
          "research.information_selection"
        ],
        "options": [
          "the reserve provides useful wetland habitat",
          "all birds prefer dry fields",
          "reeds are used only for decoration",
          "the pool is closed to every animal"
        ],
        "accepted_answers": [
          "the reserve provides useful wetland habitat"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_sanctuary:guided:1",
          "teaching_block": "Choose the detail that answers the research question and belongs to the supplied packet. Read the whole sentence, then test every option against its meaning.",
          "passage": "Question: How does the centre reduce disturbance? Packet: Visitors use a marked path; the nesting corner stays closed.",
          "prompt": "Which detail directly answers the question?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "research.information_selection"
          ],
          "options": [
            "the centre sells maps",
            "the nesting corner stays closed",
            "the path is painted blue",
            "visitors arrive in groups"
          ],
          "accepted_answers": [
            "the nesting corner stays closed"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:guided:2",
          "teaching_block": "State the packet's main idea, select relevant evidence, and avoid adding knowledge that the packet does not contain. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "Packet: A bird garden provides clean water and dense shrubs. Question: What two habitat needs are supported?",
          "prompt": "Answer in one complete sentence using both supplied facts.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "water",
              "description": "Names clean water as one supported need.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "shelter",
              "description": "Connects dense shrubs with shelter.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "water",
              "description": "Names clean water as one supported need.",
              "any_of": [
                "clean water"
              ]
            },
            {
              "id": "shelter",
              "description": "Connects dense shrubs with shelter.",
              "any_of": [
                "dense shrubs provide shelter",
                "shrubs for shelter"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 11,
          "relevance_terms": [
            "clean",
            "water",
            "dense",
            "shrubs",
            "provide"
          ],
          "model_answer": "The garden supports birds with clean water and dense shrubs that provide shelter. Reference evidence states: dense shrubs provide shelter.",
          "pass_score": 0.8
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_sanctuary:guided:3",
          "teaching_block": "Combine the related habitat details into one central idea instead of repeating a single minor fact.",
          "passage": "A wetland reserve keeps shallow pools, reed beds, and quiet nesting islands. Rangers also limit boats during breeding months.",
          "prompt": "Which sentence best states the central protection work?",
          "skill_ids": [
            "reading.paragraph_main_idea"
          ],
          "options": [
            "The reserve is famous only because boats visit it.",
            "The reserve protects feeding and nesting spaces while reducing disturbance.",
            "Every bird in the reserve eats the same food.",
            "Rangers remove all reeds before breeding season."
          ],
          "accepted_answers": [
            "The reserve protects feeding and nesting spaces while reducing disturbance."
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_sanctuary:guided:4",
          "teaching_block": "Separate supplied facts from tempting claims that the source card does not establish.",
          "passage": "Source card: the lake team counted nests from marked paths and closed one shore when chicks hatched. The card gives no population trend.",
          "prompt": "Which report remains inside the source card?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "The bird population doubled during the season.",
            "All visitors were permanently banned from the lake.",
            "The team used marked paths and closed a shore after chicks hatched.",
            "The team moved every nest to a new shore."
          ],
          "accepted_answers": [
            "The team used marked paths and closed a shore after chicks hatched."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:independent:1",
          "teaching_block": "State the packet's main idea, select relevant evidence, and avoid adding knowledge that the packet does not contain. Build the answer from two visible pieces of evidence.",
          "passage": "Packet: A marsh reserve protects reed beds, keeps a quiet nesting zone, and removes loose plastic from the water.",
          "prompt": "State the main idea and select two supporting facts.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "main",
              "description": "States that the reserve protects wetland bird habitat.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "facts",
              "description": "Selects two supplied protective actions.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "main",
              "description": "States that the reserve protects wetland bird habitat.",
              "any_of": [
                "protects wetland habitat",
                "helps birds live safely"
              ]
            },
            {
              "id": "facts",
              "description": "Selects two supplied protective actions.",
              "any_of": [
                "protects reed beds",
                "quiet nesting zone",
                "removes loose plastic"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "protects",
            "wetland",
            "habitat",
            "helps",
            "birds"
          ],
          "model_answer": "The reserve protects wetland bird habitat by keeping a quiet nesting zone and removing loose plastic from the water. Reference evidence states: protects wetland habitat.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:independent:2",
          "teaching_block": "State the packet's main idea, select relevant evidence, and avoid adding knowledge that the packet does not contain. State the relationship and support it with the relevant detail.",
          "passage": "Question: How does a hornbill use its beak? Packet: Its large beak helps pick fruit and carry food. The bird nests in tree hollows.",
          "prompt": "Report only the facts that answer the question.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "pick",
              "description": "Selects picking fruit as a beak use.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "carry",
              "description": "Selects carrying food as a beak use.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "pick",
              "description": "Selects picking fruit as a beak use.",
              "any_of": [
                "pick fruit",
                "picks fruit"
              ]
            },
            {
              "id": "carry",
              "description": "Selects carrying food as a beak use.",
              "any_of": [
                "carry food",
                "carries food"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 10,
          "relevance_terms": [
            "pick",
            "fruit",
            "picks",
            "carry",
            "food"
          ],
          "model_answer": "The hornbill uses its large beak to pick fruit and carry food.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:independent:3",
          "teaching_block": "Group the supporting actions under one protection idea, then report only the measured result supplied.",
          "passage": "At the river refuge, volunteers removed fishing line, planted native grass, and left a wide quiet zone around ground nests. Monthly checks showed fewer tangled birds near the cleaned bank.",
          "prompt": "Summarise the refuge's work and the observed result in two sentences.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
          "rubric_criteria": [
            {
              "id": "work",
              "description": "Combines the three related protection actions.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Reports the observed reduction in tangled birds.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "work",
              "description": "Combines the three related protection actions.",
              "any_of": [
                "restored a safer nesting bank"
              ]
            },
            {
              "id": "result",
              "description": "Reports the observed reduction in tangled birds.",
              "any_of": [
                "found fewer birds tangled"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "river",
            "refuge",
            "volunteers",
            "removed",
            "fishing",
            "line",
            "planted",
            "native"
          ],
          "model_answer": "Volunteers restored a safer nesting bank by removing fishing line, planting native grass, and protecting a quiet zone. Monthly checks then found fewer birds tangled near that bank.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:independent:4",
          "teaching_block": "Attribute only what the information card supports and make the missing-information boundary visible.",
          "passage": "Information card: hill sanctuary; mixed forest and open grass patches; walking allowed on two signed trails; loudspeakers prohibited; no data about ticket prices.",
          "prompt": "Write a two-sentence visitor profile using three supplied facts and one explicit information limit.",
          "skill_ids": [
            "research.information_selection",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
          "rubric_criteria": [
            {
              "id": "profile",
              "description": "Uses habitat and visitor-rule facts accurately.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "States that ticket prices are not supplied.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "profile",
              "description": "Uses habitat and visitor-rule facts accurately.",
              "any_of": [
                "mixed forest with open grass patches"
              ]
            },
            {
              "id": "limit",
              "description": "States that ticket prices are not supplied.",
              "any_of": [
                "does not provide ticket-price information"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "information",
            "card",
            "hill",
            "sanctuary",
            "mixed",
            "forest",
            "open",
            "grass"
          ],
          "model_answer": "The hill sanctuary combines mixed forest with open grass patches, and visitors may walk on two signed trails without loudspeakers. The card does not provide ticket-price information.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:transfer:1",
          "teaching_block": "State the packet's main idea, select relevant evidence, and avoid adding knowledge that the packet does not contain. Explain the first part before connecting it to the result.",
          "passage": "Packet: A coastal reserve has mudflats rich in small animals. During low tide, wading birds search the exposed mud for food.",
          "prompt": "Summarise the food relationship in your own words.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "mudflat_food",
              "description": "States that mudflats contain small animals used as food.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "low_tide",
              "description": "Explains that low tide exposes the feeding area.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "mudflat_food",
              "description": "States that mudflats contain small animals used as food.",
              "any_of": [
                "mudflats contain small animals",
                "food in exposed mud"
              ]
            },
            {
              "id": "low_tide",
              "description": "Explains that low tide exposes the feeding area.",
              "any_of": [
                "low tide exposes",
                "birds feed when mud is exposed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 13,
          "relevance_terms": [
            "mudflats",
            "contain",
            "small",
            "animals",
            "food"
          ],
          "model_answer": "At low tide, exposed mudflats give wading birds access to small animals they can eat. Reference evidence states: mudflats contain small animals; low tide exposes.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:transfer:2",
          "teaching_block": "State the packet's main idea, select relevant evidence, and avoid adding knowledge that the packet does not contain. Use your own words while preserving every required idea.",
          "passage": "Packet: Volunteers placed shallow water dishes in shade and cleaned them daily. The packet does not mention feeding bread.",
          "prompt": "Write a reliable two-detail care report and exclude the unsupported action.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "shade",
              "description": "Reports placing shallow dishes in shade.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "clean",
              "description": "Reports daily cleaning.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "shade",
              "description": "Reports placing shallow dishes in shade.",
              "any_of": [
                "shallow dishes in shade",
                "water dishes were shaded"
              ]
            },
            {
              "id": "clean",
              "description": "Reports daily cleaning.",
              "any_of": [
                "cleaned daily",
                "daily cleaning"
              ]
            }
          ],
          "forbidden_phrases": [
            "fed bread",
            "gave bread"
          ],
          "min_response_words": 11,
          "relevance_terms": [
            "shallow",
            "dishes",
            "shade",
            "water",
            "were"
          ],
          "model_answer": "Volunteers placed shallow water dishes in shade and cleaned them every day. Reference evidence states: shallow dishes in shade; cleaned daily.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:transfer:3",
          "teaching_block": "Transfer source selection into an action summary by pairing each proposal with the exact need it addresses.",
          "passage": "Town pond notes: floating litter blocks one edge; kingfishers use overhanging branches; dogs often enter the shallow corner. Proposed actions: weekly litter removal, retain the branches, add a low boundary near the corner.",
          "prompt": "Write a focused action summary that matches each problem or habitat need with the relevant proposal.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "research.information_selection",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
          "rubric_criteria": [
            {
              "id": "matching",
              "description": "Matches litter, branches, and dog entry to the correct actions.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "habitat",
              "description": "Preserves the branches used by kingfishers.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "matching",
              "description": "Matches litter, branches, and dog entry to the correct actions.",
              "any_of": [
                "removes litter from the blocked edge"
              ]
            },
            {
              "id": "habitat",
              "description": "Preserves the branches used by kingfishers.",
              "any_of": [
                "retains overhanging branches used by kingfishers"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "town",
            "pond",
            "notes",
            "floating",
            "litter",
            "blocks",
            "edge",
            "kingfishers"
          ],
          "model_answer": "The pond plan removes litter from the blocked edge, retains overhanging branches used by kingfishers, and adds a low boundary where dogs enter the shallows.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:transfer:4",
          "teaching_block": "Select only relevant packet facts, combine them around one main idea, and protect any fact the source does not give. Apply the same construct to this new passage. Use the visible passage to practise paragraph main idea and summary own words and information selection; include both details.",
          "passage": "Wetland packet: a small nesting island keeps people away from ground nests; ropes mark a no-entry edge; volunteers count nests from the opposite bank. The packet gives no bird population total.",
          "prompt": "Summarise the protection plan and state the information limit in your own words.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "summary",
          "rubric_criteria": [
            {
              "id": "wise_parrot_bird_sanctuary:transfer:4:summary",
              "description": "Combines the island, visitor boundary, and distant counting around protection.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_bird_sanctuary:transfer:4:limit",
              "description": "States that the population total is missing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_bird_sanctuary:transfer:4:summary",
              "description": "Combines the island, visitor boundary, and distant counting around protection.",
              "any_of": [
                "protects ground nests",
                "marked no-entry edge",
                "observe from the far bank"
              ]
            },
            {
              "id": "wise_parrot_bird_sanctuary:transfer:4:limit",
              "description": "States that the population total is missing.",
              "any_of": [
                "does not provide a total bird population"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "wetland",
            "protects",
            "ground"
          ],
          "model_answer": "The wetland protects ground nests by separating visitors with a marked no-entry edge while volunteers observe from the far bank. The packet does not provide a total bird population.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:review:1",
          "teaching_block": "State the packet's main idea, select relevant evidence, and avoid adding knowledge that the packet does not contain. Apply the same reasoning to a different setting and justify it.",
          "passage": "Question: Compare two supplied birds. Packet: The tailorbird stitches leaves for a nest. The weaver bird knots grass into a hanging nest.",
          "prompt": "Write a concise comparison using only packet facts.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "tailor",
              "description": "Reports the tailorbird's leaf-stitching fact.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "weaver",
              "description": "Reports the weaver bird's grass-knotting fact.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "tailor",
              "description": "Reports the tailorbird's leaf-stitching fact.",
              "any_of": [
                "tailorbird stitches leaves",
                "stitches leaf edges"
              ]
            },
            {
              "id": "weaver",
              "description": "Reports the weaver bird's grass-knotting fact.",
              "any_of": [
                "weaver bird knots grass",
                "hanging grass nest"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 13,
          "relevance_terms": [
            "tailorbird",
            "stitches",
            "leaves",
            "leaf",
            "edges"
          ],
          "model_answer": "The tailorbird stitches leaves together, while the weaver bird knots grass into a hanging nest.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:review:2",
          "teaching_block": "State the packet's main idea, select relevant evidence, and avoid adding knowledge that the packet does not contain. Separate what is stated from what can reasonably be inferred.",
          "passage": "Packet: A reserve restored one pond, planted native reeds, and recorded more nesting pairs the next season.",
          "prompt": "State the result and two actions that may have supported it without claiming certainty.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "actions",
              "description": "Names pond restoration and reed planting.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Reports more nesting pairs next season.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "caution",
              "description": "Uses cautious language rather than proving causation.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "actions",
              "description": "Names pond restoration and reed planting.",
              "any_of": [
                "restored the pond",
                "planted native reeds"
              ]
            },
            {
              "id": "result",
              "description": "Reports more nesting pairs next season.",
              "any_of": [
                "more nesting pairs",
                "increase in nesting pairs"
              ]
            },
            {
              "id": "caution",
              "description": "Uses cautious language rather than proving causation.",
              "any_of": [
                "may have supported",
                "could have helped"
              ]
            }
          ],
          "forbidden_phrases": [
            "definitely caused",
            "proved the only cause"
          ],
          "min_response_words": 15,
          "relevance_terms": [
            "restored",
            "pond",
            "planted",
            "native",
            "reeds"
          ],
          "model_answer": "Restoring the pond and planting native reeds may have supported the increase in nesting pairs recorded the next season. Reference evidence states: restored the pond.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:review:3",
          "teaching_block": "Select only relevant packet facts, combine them around one main idea, and protect any fact the source does not give. Retrieve the construct, then verify it against the passage. Use the visible passage to practise paragraph main idea and summary own words and information selection; include both details.",
          "passage": "Grassland reserve card: workers delay mowing until nesting season ends, keep one area of tall grass, and record more ground nests there. The card does not prove which single action caused the increase.",
          "prompt": "State the main idea, include two actions, and avoid a certain cause claim.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "summary",
          "rubric_criteria": [
            {
              "id": "wise_parrot_bird_sanctuary:review:3:main",
              "description": "Summarises the bird-support purpose and two actions.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_bird_sanctuary:review:3:caution",
              "description": "Reports the result without claiming a single proven cause.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_bird_sanctuary:review:3:main",
              "description": "Summarises the bird-support purpose and two actions.",
              "any_of": [
                "support nesting birds",
                "delaying mowing",
                "keeping an area of tall grass"
              ]
            },
            {
              "id": "wise_parrot_bird_sanctuary:review:3:caution",
              "description": "Reports the result without claiming a single proven cause.",
              "any_of": [
                "More nests were recorded",
                "does not prove one action caused"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "reserve",
            "changed",
            "grassland"
          ],
          "model_answer": "The reserve changed grassland care to support nesting birds by delaying mowing and keeping an area of tall grass. More nests were recorded, but the card does not prove one action caused the increase.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_sanctuary:review:4",
          "teaching_block": "Select only relevant packet facts, combine them around one main idea, and protect any fact the source does not give. Retrieve the construct, then verify it against the passage. Use the visible passage to practise paragraph main idea and summary own words and information selection; include both details.",
          "passage": "Hornbill packet: the bird nests in a tree cavity; nearby native fruit trees provide food; the reserve protects old trees and plants more fruit trees. No yearly nest count is supplied.",
          "prompt": "Write a focused habitat summary and protect the missing count.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "interaction_type": "summary",
          "rubric_criteria": [
            {
              "id": "wise_parrot_bird_sanctuary:review:4:habitat",
              "description": "Links protected cavities and fruit planting to habitat needs.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_bird_sanctuary:review:4:boundary",
              "description": "States that the yearly count is absent.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_bird_sanctuary:review:4:habitat",
              "description": "Links protected cavities and fruit planting to habitat needs.",
              "any_of": [
                "protecting old cavity trees",
                "planting native fruit trees"
              ]
            },
            {
              "id": "wise_parrot_bird_sanctuary:review:4:boundary",
              "description": "States that the yearly count is absent.",
              "any_of": [
                "supplies no yearly nest count"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "reserve",
            "supports",
            "hornbills"
          ],
          "model_answer": "The reserve supports hornbills by protecting old cavity trees for nesting and planting native fruit trees for food. The packet supplies no yearly nest count.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "fact-selection-or-invention",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.summary_own_words",
            "research.information_selection"
          ],
          "misconception": "The learner copies every packet detail, misses the research question, or adds an attractive fact that the supplied source never states.",
          "remediation": "Restate the research question, mark only details that answer it, and label any outside knowledge as excluded before writing the summary.",
          "support_check_ids": [
            "wise_parrot_bird_sanctuary:support:bridge",
            "wise_parrot_bird_sanctuary:support:masterclass",
            "wise_parrot_bird_sanctuary:support:revision_level_1",
            "wise_parrot_bird_sanctuary:support:revision_level_2",
            "wise_parrot_bird_sanctuary:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_sanctuary:support:bridge",
          "teaching_block": "Choose the detail that answers the research question and belongs to the supplied packet. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "Question: Where can birds shelter? Packet: Dense reeds border the northern pool; an open lawn lies near the gate.",
          "prompt": "Which fact should be selected?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "research.information_selection"
          ],
          "options": [
            "the gate has a lawn",
            "the northern pool has dense reeds",
            "the lawn is open",
            "the reserve has visitors"
          ],
          "accepted_answers": [
            "the northern pool has dense reeds"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_sanctuary:support:masterclass",
          "teaching_block": "Choose the detail that answers the research question and belongs to the supplied packet. Reject any option that adds a fact the passage never gives.",
          "passage": "Packet: Volunteers count nests each week and record changes without touching them.",
          "prompt": "Which statement is supported?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "research.information_selection"
          ],
          "options": [
            "volunteers monitor nests carefully",
            "volunteers move every nest",
            "counts happen once a year",
            "records are unnecessary"
          ],
          "accepted_answers": [
            "volunteers monitor nests carefully"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_sanctuary:support:revision_level_1",
          "teaching_block": "Choose the detail that answers the research question and belongs to the supplied packet. Break the task into one smaller decision and check it carefully.",
          "passage": "Question: Which bird is adapted for wading? Packet: Bird A has long legs for shallow water. Bird B has a short beak for cracking seed.",
          "prompt": "Which fact answers the question?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "research.information_selection"
          ],
          "options": [
            "Bird A has long legs",
            "Bird B cracks seed",
            "both birds have feathers",
            "the packet names two birds"
          ],
          "accepted_answers": [
            "Bird A has long legs"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_sanctuary:support:revision_level_2",
          "teaching_block": "Choose the detail that answers the research question and belongs to the supplied packet. Name the rule first, then apply it to this new example.",
          "passage": "Packet: A macaw has a strong curved beak and uses it to crack hard food.",
          "prompt": "Which two details belong together?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "research.information_selection"
          ],
          "options": [
            "strong curved beak and cracking hard food",
            "bright feathers and quiet water",
            "long legs and deep diving",
            "small feet and digging tunnels"
          ],
          "accepted_answers": [
            "strong curved beak and cracking hard food"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_sanctuary:support:revision_level_3",
          "teaching_block": "Choose the detail that answers the research question and belongs to the supplied packet. Compare the tempting error with the evidence that corrects it.",
          "passage": "Packet: The sanctuary closes one trail in nesting season but keeps the viewing platform open.",
          "prompt": "Which summary is accurate?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "research.information_selection"
          ],
          "options": [
            "all visitors are banned forever",
            "access is managed to protect nesting birds",
            "birds are moved to the platform",
            "the trail is widened during nesting"
          ],
          "accepted_answers": [
            "access is managed to protect nesting birds"
          ]
        }
      }
    },
    {
      "level_id": "wise_parrot_story_continuation",
      "title": "Continue a story with purpose",
      "focus": "develop an organised past-tense paragraph",
      "outcome": "Write a coherent continuation with a connected opening, reasoned action, developed result, and mainly consistent past tense.",
      "skill_ids": [
        "writing.paragraph",
        "grammar.tense_usage"
      ],
      "episode_kind": "expression_workshop",
      "source_anchor_ids": [
        "eng_c5_ch04:write:10"
      ],
      "connect": {
        "teaching_block": "A strong continuation grows from the final situation, gives the character a reasoned next action, develops what happens, and closes the new event.",
        "passage": "A freed bird reaches a neem tree and notices a torn kite thread around a branch. A useful continuation explains what it notices, chooses an action, and shows the outcome.",
        "prompt": "Continue when you can explain how this example helps you develop an organised past-tense paragraph."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "wise_parrot_story_continuation:co_construct",
        "teaching_block": "Check whether the verb form and event choice belong to a completed past-tense continuation. Locate the exact clue before comparing the choices.",
        "passage": "Yesterday the parrot ___ across the river before resting.",
        "prompt": "Which verb form fits the completed event?",
        "skill_ids": [
          "grammar.tense_usage"
        ],
        "options": [
          "flies",
          "flew",
          "will fly",
          "is flying"
        ],
        "accepted_answers": [
          "flew"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_continuation:guided:1",
          "teaching_block": "Check whether the verb form and event choice belong to a completed past-tense continuation. Read the whole sentence, then test every option against its meaning.",
          "passage": "The bird noticed a loose thread and ___ towards it carefully.",
          "prompt": "Which past-tense verb fits?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "moves",
            "moved",
            "moving",
            "will move"
          ],
          "accepted_answers": [
            "moved"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:guided:2",
          "teaching_block": "Develop the new scene as one focused paragraph with connected past events and a clear result. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "The parrot reached a grove and saw plastic thread hanging near a nest.",
          "prompt": "Write two connected past-tense sentences: one states what it noticed and one explains its safe next action.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "notice",
              "description": "States the plastic-thread danger in past tense.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Gives a safe reasoned action in past tense.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "notice",
              "description": "States the plastic-thread danger in past tense.",
              "any_of": [
                "noticed plastic thread",
                "saw thread near the nest"
              ]
            },
            {
              "id": "action",
              "description": "Gives a safe reasoned action in past tense.",
              "any_of": [
                "called a gardener",
                "warned the flock",
                "because it was dangerous"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "noticed",
            "plastic",
            "thread",
            "near",
            "nest"
          ],
          "model_answer": "The parrot noticed plastic thread hanging near the nest. Because pulling it alone could be dangerous, he called a gardener for help.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:guided:3",
          "teaching_block": "Carry forward the stated obstacle and use a second event that grows directly from the first.",
          "passage": "A released parrot reaches the forest at dusk, but the flock has moved beyond a swollen stream. A narrow branch still connects the two banks.",
          "prompt": "Write the next two connected events, keeping the setting and past tense consistent.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "crossing",
              "description": "Develops a believable response to the swollen stream.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "continuity",
              "description": "Uses the flock's calls to continue the search.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "crossing",
              "description": "Develops a believable response to the swollen stream.",
              "any_of": [
                "tested the narrow branch before crossing"
              ]
            },
            {
              "id": "continuity",
              "description": "Uses the flock's calls to continue the search.",
              "any_of": [
                "followed the flock's calls"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "released",
            "parrot",
            "reaches",
            "forest",
            "dusk",
            "flock",
            "moved",
            "beyond"
          ],
          "model_answer": "The parrot tested the narrow branch before crossing the stream. From the far bank, it followed the flock's calls into the trees.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "crossing",
            "continuity"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_story_continuation:guided:4",
          "teaching_block": "Choose a plausible next event and keep all completed narrative actions in the same past-time frame.",
          "passage": "Meera found an injured myna beside the path. She called the rescue centre and waited at a safe distance.",
          "prompt": "Which sentence continues the episode in consistent past tense?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "A trained volunteer arrives and will placed the myna.",
            "Meera carried every wild bird home by herself.",
            "The path becomes a river before yesterday.",
            "A trained volunteer arrived and placed the myna in a ventilated carrier."
          ],
          "accepted_answers": [
            "A trained volunteer arrived and placed the myna in a ventilated carrier."
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:independent:1",
          "teaching_block": "Develop the new scene as one focused paragraph with connected past events and a clear result. Build the answer from two visible pieces of evidence.",
          "passage": "After escaping, the parrot found a young bird tangled in loose thread beside a bush.",
          "prompt": "Write a 45 to 70 word continuation showing what it noticed, why it acted, how it helped, and the result.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "opening",
              "description": "Connects directly to finding the tangled young bird.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason_action",
              "description": "Shows a sensible helping action and reason.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Ends with a clear outcome.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "past",
              "description": "Uses past tense consistently.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "opening",
              "description": "Connects directly to finding the tangled young bird.",
              "any_of": [
                "found the young bird",
                "noticed the tangled bird"
              ]
            },
            {
              "id": "reason_action",
              "description": "Shows a sensible helping action and reason.",
              "any_of": [
                "wanted to help",
                "called a rescuer",
                "loosened the safe part"
              ]
            },
            {
              "id": "result",
              "description": "Ends with a clear outcome.",
              "any_of": [
                "bird was freed",
                "reached safety"
              ]
            },
            {
              "id": "past",
              "description": "Uses past tense consistently.",
              "any_of": [
                "noticed",
                "helped",
                "flew"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "found",
            "young",
            "bird",
            "noticed",
            "tangled"
          ],
          "model_answer": "The parrot noticed that loose thread held the young bird's wing. Because pulling could hurt it, he called other birds until a gardener came. The gardener cut the thread carefully, and the young bird stretched its wing. Soon both birds flew to a safe branch together. Reference evidence states: found the young bird; wanted to help; bird was freed.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:independent:2",
          "teaching_block": "Develop the new scene as one focused paragraph with connected past events and a clear result. State the relationship and support it with the relevant detail.",
          "passage": "The freed parrot reached the forest just before a storm and saw a chick alone on a low branch.",
          "prompt": "Continue the scene in 45 to 70 words with a reasoned choice, developed action, and closing result.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "storm",
              "description": "Uses the approaching storm and chick as the opening situation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "choice",
              "description": "Gives the parrot a sensible reasoned choice.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "development",
              "description": "Shows how the help happens.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "ending",
              "description": "Closes with a clear safe result.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "storm",
              "description": "Uses the approaching storm and chick as the opening situation.",
              "any_of": [
                "storm was approaching",
                "chick on a low branch"
              ]
            },
            {
              "id": "choice",
              "description": "Gives the parrot a sensible reasoned choice.",
              "any_of": [
                "decided to guide",
                "because the branch was exposed"
              ]
            },
            {
              "id": "development",
              "description": "Shows how the help happens.",
              "any_of": [
                "called the flock",
                "guided the chick"
              ]
            },
            {
              "id": "ending",
              "description": "Closes with a clear safe result.",
              "any_of": [
                "reached shelter",
                "stayed safe"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "storm",
            "approaching",
            "chick",
            "branch",
            "decided"
          ],
          "model_answer": "Dark clouds gathered as the parrot spotted a chick on an exposed branch. He decided to guide it towards thicker leaves because heavy rain was near. He called softly, flew ahead, and waited at each branch. The chick followed, and both reached a sheltered tree before the storm began. Reference evidence states: storm was approaching; called the flock; reached shelter.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:independent:3",
          "teaching_block": "Plan problem, reasoned action, and result before drafting; maintain past tense and causal continuity throughout.",
          "passage": "After escaping, a young bird finds its old tree cut down. It hears familiar calls from a grove across a busy road.",
          "prompt": "Write a 45 to 70 word continuation with a clear problem, a safe action, and a resolved ending.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "problem",
              "description": "Uses the missing tree and separated flock as the problem.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safe_action",
              "description": "Develops a safe crossing action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "ending",
              "description": "Closes with reunion before nightfall.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "problem",
              "description": "Uses the missing tree and separated flock as the problem.",
              "any_of": [
                "heard the flock across the road"
              ]
            },
            {
              "id": "safe_action",
              "description": "Develops a safe crossing action.",
              "any_of": [
                "rose above the rooftops and crossed safely"
              ]
            },
            {
              "id": "ending",
              "description": "Closes with reunion before nightfall.",
              "any_of": [
                "settled beside them before nightfall"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "after",
            "escaping",
            "young",
            "bird",
            "finds",
            "tree",
            "down",
            "hears"
          ],
          "model_answer": "The bird circled above the missing tree until it heard the flock across the road. Instead of flying low through traffic, it rose above the rooftops and crossed safely. The flock answered its call from a neem grove, and the tired bird settled beside them before nightfall.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "problem",
            "safe_action",
            "ending"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:independent:4",
          "teaching_block": "Use the viewpoint to explain thought before action, then connect the final move to the visible setting clue.",
          "passage": "A shopkeeper opens an old cage, but the bird remains on the perch and watches the unfamiliar courtyard. A guava tree stands near the wall.",
          "prompt": "Continue from the bird's viewpoint in 45 to 70 words, explaining its hesitation, decision, and first safe move.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "hesitation",
              "description": "Explains hesitation through the unfamiliar sounds.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Shows the bird judging a safe route.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "move",
              "description": "Ends with a first safe move to the tree.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "hesitation",
              "description": "Explains hesitation through the unfamiliar sounds.",
              "any_of": [
                "waited because every sound"
              ]
            },
            {
              "id": "decision",
              "description": "Shows the bird judging a safe route.",
              "any_of": [
                "studied the guava tree and judged"
              ]
            },
            {
              "id": "move",
              "description": "Ends with a first safe move to the tree.",
              "any_of": [
                "flew to a low branch"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "shopkeeper",
            "opens",
            "cage",
            "bird",
            "remains",
            "perch",
            "watches",
            "unfamiliar"
          ],
          "model_answer": "The open door looked inviting, yet the bird waited because every sound in the courtyard was new. When the lane grew quiet, it studied the guava tree and judged the short distance. It hopped to the doorway, flew to a low branch, and rested there while learning the new surroundings.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "hesitation",
            "decision",
            "move"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:transfer:1",
          "teaching_block": "Develop the new scene as one focused paragraph with connected past events and a clear result. Explain the first part before connecting it to the result.",
          "passage": "A myna left a small cage and landed in a crowded market where it had never flown before.",
          "prompt": "Write a focused 45 to 70 word continuation with past-tense events and a resolved problem.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "connection",
              "description": "Begins with the myna in the unfamiliar market.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "problem",
              "description": "Develops one clear market problem.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Shows a sensible action to solve it.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Ends with a resolved outcome.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "connection",
              "description": "Begins with the myna in the unfamiliar market.",
              "any_of": [
                "landed in the market",
                "unfamiliar market"
              ]
            },
            {
              "id": "problem",
              "description": "Develops one clear market problem.",
              "any_of": [
                "noise confused",
                "could not find trees"
              ]
            },
            {
              "id": "action",
              "description": "Shows a sensible action to solve it.",
              "any_of": [
                "followed other birds",
                "flew above the stalls"
              ]
            },
            {
              "id": "result",
              "description": "Ends with a resolved outcome.",
              "any_of": [
                "reached a tree",
                "found a quiet park"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "landed",
            "market",
            "unfamiliar",
            "noise",
            "confused"
          ],
          "model_answer": "The unfamiliar market noise confused the myna, and tall awnings blocked its view. It flew above the stalls and followed two pigeons towards a line of trees. Beyond the shops, it found a quiet park with water and shade. The myna rested there until it felt ready to explore again.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:transfer:2",
          "teaching_block": "Develop the new scene as one focused paragraph with connected past events and a clear result. Use your own words while preserving every required idea.",
          "passage": "A rescued pigeon was released near its old neighbourhood but found its usual water place dry.",
          "prompt": "Continue in 45 to 70 words, showing the problem, a sensible response, and the final result.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "problem",
              "description": "States that the usual water place is dry.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "response",
              "description": "Develops a sensible search or help action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Ends with access to safe water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "past",
              "description": "Maintains past-tense narration.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "problem",
              "description": "States that the usual water place is dry.",
              "any_of": [
                "water place was dry",
                "found no water"
              ]
            },
            {
              "id": "response",
              "description": "Develops a sensible search or help action.",
              "any_of": [
                "searched nearby",
                "followed other birds",
                "volunteer placed water"
              ]
            },
            {
              "id": "result",
              "description": "Ends with access to safe water.",
              "any_of": [
                "found clean water",
                "drank safely"
              ]
            },
            {
              "id": "past",
              "description": "Maintains past-tense narration.",
              "any_of": [
                "searched",
                "followed",
                "found"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "water",
            "place",
            "found",
            "searched",
            "nearby"
          ],
          "model_answer": "The pigeon circled the dry corner and then followed sparrows towards a shaded courtyard. A volunteer had placed a shallow bowl there and cleaned it that morning. The pigeon landed nearby, watched for a moment, and drank safely. It later returned with two other birds. Reference evidence states: water place was dry; searched nearby.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:transfer:3",
          "teaching_block": "Transfer narrative structure rather than story details: establish the obstacle, develop a plausible response, and close the outcome.",
          "passage": "A rescued turtle is released beside a lake. On its way to the water, a plastic ring blocks the direct path while reeds offer a longer route.",
          "prompt": "Write a 45 to 70 word continuation that transfers problem-action-result structure to this new animal story.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "problem",
              "description": "Establishes the blocked direct path.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "response",
              "description": "Uses the reeds as the turtle's alternate route.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Closes with the turtle reaching the lake.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "problem",
              "description": "Establishes the blocked direct path.",
              "any_of": [
                "plastic ring blocked the direct path"
              ]
            },
            {
              "id": "response",
              "description": "Uses the reeds as the turtle's alternate route.",
              "any_of": [
                "turned toward the reeds"
              ]
            },
            {
              "id": "result",
              "description": "Closes with the turtle reaching the lake.",
              "any_of": [
                "animal reached the clear water"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "rescued",
            "turtle",
            "released",
            "beside",
            "lake",
            "water",
            "plastic",
            "ring"
          ],
          "model_answer": "The turtle stopped when the plastic ring blocked the direct path. It turned toward the reeds and moved slowly through the softer ground instead. A volunteer removed the ring without touching the turtle. Soon the animal reached the clear water, paused at the edge, and disappeared beneath the surface.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "problem",
            "response",
            "result"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:transfer:4",
          "teaching_block": "Continue from the given problem with connected past-tense actions, a believable result, and a clear ending. Apply the same construct to this new passage. Use the visible passage to practise paragraph and tense usage; include both details.",
          "passage": "A young squirrel left the rescue basket just as rainwater began rushing across the shortest path to an old neem tree.",
          "prompt": "Write a 45 to 70 word continuation with a safe choice, ordered past-tense action, and a resolved ending.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "wise_parrot_story_continuation:transfer:4:plot",
              "description": "Develops the water problem, safer route, and resolved arrival.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_story_continuation:transfer:4:craft",
              "description": "Uses connected past-tense action and a safe ending.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_story_continuation:transfer:4:plot",
              "description": "Develops the water problem, safer route, and resolved arrival.",
              "any_of": [
                "watched leaves spin",
                "climbed along the log",
                "reached a low neem branch"
              ]
            },
            {
              "id": "wise_parrot_story_continuation:transfer:4:craft",
              "description": "Uses connected past-tense action and a safe ending.",
              "any_of": [
                "volunteer quietly moved",
                "disappeared safely"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "squirrel",
            "paused",
            "beside"
          ],
          "model_answer": "The squirrel paused beside a dry log and watched leaves spin through the fast water. Instead of crossing, it climbed along the log to a higher wall. A volunteer quietly moved people back, giving it space. From the wall, the squirrel reached a low neem branch and disappeared safely into the leaves.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:review:1",
          "teaching_block": "Develop the new scene as one focused paragraph with connected past events and a clear result. Apply the same reasoning to a different setting and justify it.",
          "passage": "The parrot joined a flock, but one young bird was afraid to cross an open field.",
          "prompt": "Write a 45 to 70 word ending that shows support without forcing the young bird.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "fear",
              "description": "Keeps the young bird's fear as the central problem.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "support",
              "description": "Shows patient, non-forcing support.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Ends with a believable choice or progress.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "fear",
              "description": "Keeps the young bird's fear as the central problem.",
              "any_of": [
                "afraid of the open field",
                "young bird hesitated"
              ]
            },
            {
              "id": "support",
              "description": "Shows patient, non-forcing support.",
              "any_of": [
                "waited",
                "demonstrated",
                "flew beside"
              ]
            },
            {
              "id": "result",
              "description": "Ends with a believable choice or progress.",
              "any_of": [
                "crossed when ready",
                "reached the trees"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "afraid",
            "open",
            "field",
            "young",
            "bird"
          ],
          "model_answer": "The young bird hesitated at the edge of the field. Instead of pushing it, the parrot waited and showed a shorter route between two shrubs. He flew beside the youngster at a steady pace. When it felt ready, the young bird crossed the gap and reached the next trees safely. Reference evidence states: crossed when ready.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:review:2",
          "teaching_block": "Develop the new scene as one focused paragraph with connected past events and a clear result. Separate what is stated from what can reasonably be inferred.",
          "passage": "At dusk, the parrot returned to thank the forest bird that had sent the silent clue.",
          "prompt": "Write a 45 to 70 word concluding paragraph with dialogue, action, and a closing idea.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "meeting",
              "description": "Connects to returning to thank the forest bird.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "dialogue",
              "description": "Includes a brief relevant exchange.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Adds one connected action after the exchange.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "closing",
              "description": "Ends with a clear concluding idea.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "meeting",
              "description": "Connects to returning to thank the forest bird.",
              "any_of": [
                "returned to thank",
                "met the forest bird"
              ]
            },
            {
              "id": "dialogue",
              "description": "Includes a brief relevant exchange.",
              "any_of": [
                "thank you",
                "the bird replied"
              ]
            },
            {
              "id": "action",
              "description": "Adds one connected action after the exchange.",
              "any_of": [
                "joined the flock",
                "flew together"
              ]
            },
            {
              "id": "closing",
              "description": "Ends with a clear concluding idea.",
              "any_of": [
                "felt at home",
                "freedom shared"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "returned",
            "thank",
            "forest",
            "bird",
            "replied"
          ],
          "model_answer": "At dusk, the parrot found the forest bird beneath the old tree. 'Your silent clue gave me a chance to fly,' he said. The forest bird replied that understanding the clue had required courage too. They joined the flock, flew above the river, and returned together as the sky grew dark. Reference evidence states: returned to thank; thank you; felt at home.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:review:3",
          "teaching_block": "Continue from the given problem with connected past-tense actions, a believable result, and a clear ending. Retrieve the construct, then verify it against the passage. Use the visible passage to practise paragraph and tense usage; include both details.",
          "passage": "A crane stepped out of the care enclosure and saw a loop of discarded fishing line beside the marsh path.",
          "prompt": "Continue for 45 to 70 words with a believable problem, careful response, and final movement toward freedom.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "wise_parrot_story_continuation:review:3:response",
              "description": "Shows the crane stopping and the ranger clearing the danger.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_story_continuation:review:3:ending",
              "description": "Closes with an unforced past-tense move to the water.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_story_continuation:review:3:response",
              "description": "Shows the crane stopping and the ranger clearing the danger.",
              "any_of": [
                "crane stopped before the line",
                "ranger noticed the danger",
                "lifted the loop"
              ]
            },
            {
              "id": "wise_parrot_story_continuation:review:3:ending",
              "description": "Closes with an unforced past-tense move to the water.",
              "any_of": [
                "spread its wings",
                "landed beside the open water"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "crane",
            "stopped",
            "called"
          ],
          "model_answer": "The crane stopped before the line and called sharply. A ranger noticed the danger, asked visitors to wait, and lifted the loop with a long tool. When the path was clear, the crane spread its wings, crossed the reeds, and landed beside the open water without being chased.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:review:4",
          "teaching_block": "Continue from the given problem with connected past-tense actions, a believable result, and a clear ending. Retrieve the construct, then verify it against the passage. Use the visible passage to practise paragraph and tense usage; include both details.",
          "passage": "A young parakeet followed its flock from the garden, but a sudden wind pushed it toward an unfamiliar balcony.",
          "prompt": "Write a 45 to 70 word ending that uses observation rather than force to solve the separation.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "wise_parrot_story_continuation:review:4:solution",
              "description": "Uses waiting, listening, and the flock call to solve the problem.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_story_continuation:review:4:close",
              "description": "Ends with reunion and a reasoned reflection.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_story_continuation:review:4:solution",
              "description": "Uses waiting, listening, and the flock call to solve the problem.",
              "any_of": [
                "until the gust weakened",
                "answered a distant flock call",
                "flew toward their sound"
              ]
            },
            {
              "id": "wise_parrot_story_continuation:review:4:close",
              "description": "Ends with reunion and a reasoned reflection.",
              "any_of": [
                "joined them over the trees",
                "waited for a safe moment"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 45,
          "relevance_terms": [
            "parakeet",
            "gripped",
            "railing"
          ],
          "model_answer": "The parakeet gripped the railing until the gust weakened. It listened, then answered a distant flock call from the park. The other birds circled back above the building, and the parakeet flew toward their sound. Soon it joined them over the trees, having waited for a safe moment instead of struggling against the wind.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response"
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "continuation-list-or-tense-drift",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "misconception": "The learner writes disconnected actions, changes tense unpredictably, or jumps from the opening problem straight to an unexplained ending.",
          "remediation": "Plan four boxes for connection, reasoned choice, developed action, and result; then underline every main verb and repair tense drift.",
          "support_check_ids": [
            "wise_parrot_story_continuation:support:bridge",
            "wise_parrot_story_continuation:support:masterclass",
            "wise_parrot_story_continuation:support:revision_level_1",
            "wise_parrot_story_continuation:support:revision_level_2",
            "wise_parrot_story_continuation:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:support:bridge",
          "teaching_block": "Build three connected parts: begin from the supplied event, show one sensible helping action, and end with its result. Keep the events in past tense.",
          "passage": "A strong wind knocked a fledgling from a low branch. The parrot landed beside it and saw that the bird was frightened but not hurt.",
          "prompt": "Write a 25 to 40 word continuation with a connected opening, a safe helping action, and a clear result.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "opening",
              "description": "Connects directly to the frightened fledgling.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Shows a sensible safe helping action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Ends with a clear result.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "past",
              "description": "Uses past tense for the continued events.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "opening",
              "description": "Connects directly to the frightened fledgling.",
              "any_of": [
                "frightened fledgling",
                "young bird"
              ]
            },
            {
              "id": "action",
              "description": "Shows a sensible safe helping action.",
              "any_of": [
                "called the parent birds",
                "guided it to shelter",
                "stayed beside it"
              ]
            },
            {
              "id": "result",
              "description": "Ends with a clear result.",
              "any_of": [
                "reached a safe branch",
                "parent birds returned",
                "bird became calm"
              ]
            },
            {
              "id": "past",
              "description": "Uses past tense for the continued events.",
              "any_of": [
                "called",
                "guided",
                "stayed",
                "returned"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "fledgling",
            "parrot",
            "help",
            "safe",
            "result"
          ],
          "model_answer": "The parrot stayed beside the frightened fledgling and called the parent birds toward the nearby trees. Its parents returned and guided it through the bushes. Soon the young bird reached a safe branch and became calm.",
          "pass_score": 0.8
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:support:masterclass",
          "teaching_block": "Plan the paragraph before writing: restate the new problem, explain why the character chose an action, develop that action, and close with the outcome.",
          "passage": "At the orchard, the parrot noticed a loose net hanging across a narrow flight path. A caretaker was working near the gate.",
          "prompt": "Write a 35 to 55 word continuation in which the parrot responds safely and the problem is resolved. Keep the events connected and in past tense.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "problem",
              "description": "Begins from the loose net in the flight path.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason_action",
              "description": "Explains a safe action and why it was chosen.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Develops a believable resolution.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "past",
              "description": "Keeps the narrated events mainly in past tense.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "problem",
              "description": "Begins from the loose net in the flight path.",
              "any_of": [
                "loose net",
                "blocked flight path"
              ]
            },
            {
              "id": "reason_action",
              "description": "Explains a safe action and why it was chosen.",
              "any_of": [
                "called the caretaker",
                "did not pull the net",
                "warned the other birds"
              ]
            },
            {
              "id": "result",
              "description": "Develops a believable resolution.",
              "any_of": [
                "caretaker removed the net",
                "path became safe",
                "birds crossed safely"
              ]
            },
            {
              "id": "past",
              "description": "Keeps the narrated events mainly in past tense.",
              "any_of": [
                "noticed",
                "called",
                "removed",
                "crossed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 35,
          "relevance_terms": [
            "net",
            "flight",
            "caretaker",
            "safe",
            "removed"
          ],
          "model_answer": "The parrot noticed that the loose net could trap birds using the narrow path. Instead of tugging it, he warned the flock and called the caretaker. She removed the net, the path became safe, and the birds crossed the orchard without danger.",
          "pass_score": 0.8
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:support:revision_level_1",
          "teaching_block": "Use a simple paragraph frame: what changed, what the parrot did, and what happened next. Join the three parts rather than listing them separately.",
          "passage": "Rain flooded the shallow feeding tray, and the scattered seeds began to float away.",
          "prompt": "Write a 20 to 35 word continuation showing the parrot's response and the result in past tense.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "opening",
              "description": "Starts from the flooded tray and floating seeds.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Adds a sensible response by the parrot.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Ends with a connected result.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "opening",
              "description": "Starts from the flooded tray and floating seeds.",
              "any_of": [
                "tray flooded",
                "seeds floated"
              ]
            },
            {
              "id": "action",
              "description": "Adds a sensible response by the parrot.",
              "any_of": [
                "called the gardener",
                "moved the tray",
                "covered the seeds"
              ]
            },
            {
              "id": "result",
              "description": "Ends with a connected result.",
              "any_of": [
                "seeds were saved",
                "tray was moved",
                "birds ate later"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 20,
          "relevance_terms": [
            "tray",
            "seeds",
            "parrot",
            "help",
            "result"
          ],
          "model_answer": "The parrot called the gardener when the seeds floated from the flooded tray. She moved the tray under the roof, and the seeds were saved so the birds could feed after the rain stopped.",
          "pass_score": 0.8
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:support:revision_level_2",
          "teaching_block": "Make the reason visible between the opening and action. Then add a result that follows from that action and keep the verbs in the past.",
          "passage": "The parrot heard repeated tapping from a closed garden shed. The gardener was watering plants nearby.",
          "prompt": "Write a 22 to 38 word continuation explaining why the parrot acted, what it did, and what the gardener discovered.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "creative_continuation",
          "rubric_criteria": [
            {
              "id": "reason",
              "description": "Uses the repeated tapping as the reason to act.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Shows the parrot alerting the nearby gardener.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "Adds a plausible discovery and outcome.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "reason",
              "description": "Uses the repeated tapping as the reason to act.",
              "any_of": [
                "heard repeated tapping",
                "sound came from the shed"
              ]
            },
            {
              "id": "action",
              "description": "Shows the parrot alerting the nearby gardener.",
              "any_of": [
                "called the gardener",
                "led her to the shed"
              ]
            },
            {
              "id": "result",
              "description": "Adds a plausible discovery and outcome.",
              "any_of": [
                "opened the shed",
                "found a trapped bird",
                "bird flew out"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "tapping",
            "shed",
            "gardener",
            "parrot",
            "found"
          ],
          "model_answer": "The parrot heard repeated tapping, so he called the gardener and led her to the shed. She opened the door and found a small bird inside. The bird flew out safely, and the tapping stopped.",
          "pass_score": 0.8
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "wise_parrot_story_continuation:support:revision_level_3",
          "teaching_block": "Close the story by linking a remembered problem to a changed situation. Use two or more connected past events and finish with what the character understood.",
          "passage": "The next morning, the parrot returned to the orchard and saw the repaired feeder hanging firmly beneath the roof.",
          "prompt": "Write a 22 to 40 word closing paragraph showing what the parrot checked, what happened next, and what it learned.",
          "skill_ids": [
            "writing.paragraph",
            "grammar.tense_usage"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "check",
              "description": "Shows the parrot checking the repaired feeder.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "Adds a connected event after the check.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "learning",
              "description": "Ends with a sensible lesson from the event.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "check",
              "description": "Shows the parrot checking the repaired feeder.",
              "any_of": [
                "checked the feeder",
                "saw it was firm"
              ]
            },
            {
              "id": "next",
              "description": "Adds a connected event after the check.",
              "any_of": [
                "birds returned",
                "ate safely",
                "feeder stayed steady"
              ]
            },
            {
              "id": "learning",
              "description": "Ends with a sensible lesson from the event.",
              "any_of": [
                "careful help solved the problem",
                "asking for help kept others safe"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 22,
          "relevance_terms": [
            "feeder",
            "checked",
            "birds",
            "safe",
            "learned"
          ],
          "model_answer": "The parrot checked the feeder and saw that it stayed firm in the wind. Soon the birds returned and ate safely. He learned that careful help solved the problem and kept the flock safe.",
          "pass_score": 0.8
        }
      }
    },
    {
      "level_id": "wise_parrot_bird_care_procedure",
      "title": "Plan safe bird care steps",
      "focus": "select facts and explain an ordered procedure",
      "outcome": "Use a bounded source packet to write materials, ordered actions, safety guidance, and an intended result for a simple bird-care procedure.",
      "skill_ids": [
        "writing.procedure",
        "research.information_selection",
        "writing.complete_sentence"
      ],
      "episode_kind": "application_mission",
      "source_anchor_ids": [
        "eng_c5_ch04:explore:12"
      ],
      "connect": {
        "teaching_block": "A safe procedure names suitable materials, orders each action, includes a safety condition, and explains the intended care result.",
        "passage": "Source card: use a shallow clean bowl, place it in shade, refill it daily, and ask an adult to choose a stable outdoor spot. These facts become ordered steps, not a loose list.",
        "prompt": "Continue when you can explain how this example helps you select facts and explain an ordered procedure."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "wise_parrot_bird_care_procedure:co_construct",
        "teaching_block": "Select the supplied fact that belongs to the requested procedure stage. Locate the exact clue before comparing the choices.",
        "passage": "Source card: shallow bowl; clean water; shaded stable place; daily cleaning.",
        "prompt": "Which item belongs in the materials list?",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "a deep metal drum",
          "a shallow bowl",
          "loose wire",
          "sweetened drink"
        ],
        "accepted_answers": [
          "a shallow bowl"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_care_procedure:guided:1",
          "teaching_block": "Select the supplied fact that belongs to the requested procedure stage. Read the whole sentence, then test every option against its meaning.",
          "passage": "Steps: clean bowl; add water; place in shade; check daily.",
          "prompt": "Which action comes first?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "place in shade",
            "check next week",
            "clean the bowl",
            "add bread"
          ],
          "accepted_answers": [
            "clean the bowl"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:guided:2",
          "teaching_block": "Write a complete ordered procedure using only safe supplied facts and a clear final purpose. Build the response with the supplied scaffold, then check every required idea.",
          "passage": "Notes: clean bowl; fresh water; shade; adult chooses the stable spot.",
          "prompt": "Write two complete ordered sentences that include the action and safety condition.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "actions",
              "description": "Orders cleaning before adding fresh water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safety",
              "description": "Includes shade and adult-selected stable placement.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "actions",
              "description": "Orders cleaning before adding fresh water.",
              "any_of": [
                "clean the bowl",
                "add fresh water"
              ]
            },
            {
              "id": "safety",
              "description": "Includes shade and adult-selected stable placement.",
              "any_of": [
                "adult chooses",
                "stable spot",
                "in shade"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 17,
          "relevance_terms": [
            "clean",
            "bowl",
            "fresh",
            "water",
            "adult"
          ],
          "model_answer": "First clean the bowl and add fresh water. Then ask an adult to place it in a stable shaded spot. Reference evidence states: adult chooses.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "actions",
            "safety"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_care_procedure:guided:3",
          "teaching_block": "Arrange the supplied actions by preparation, refill, placement, and safety condition without inventing extra materials.",
          "passage": "Source card: refill a bird-water tray daily; rinse away slime first; place it in shade; ask an adult to move a heavy tray.",
          "prompt": "Which sequence uses the source safely?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "Refill over the slime and leave the tray in full sun.",
            "Lift every heavy tray alone before rinsing it.",
            "Rinse the tray, refill it, place it in shade, and ask an adult to move it if heavy.",
            "Add soap to the drinking water after placing it outside."
          ],
          "accepted_answers": [
            "Rinse the tray, refill it, place it in shade, and ask an adult to move it if heavy."
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:guided:4",
          "teaching_block": "Convert the source card into one complete sentence with explicit order words and the adult-help condition.",
          "passage": "A window sticker can warn birds about clear glass. The card says: clean one outside corner, ask an adult to help, place the sticker, then check that it is secure.",
          "prompt": "Write the four actions as one ordered procedure sentence.",
          "skill_ids": [
            "writing.procedure",
            "writing.complete_sentence"
          ],
          "interaction_type": "short_text",
          "rubric_criteria": [
            {
              "id": "prepare",
              "description": "Begins by cleaning the outside corner with adult help.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "place",
              "description": "Places the warning sticker after preparation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "check",
              "description": "Ends by checking security.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "prepare",
              "description": "Begins by cleaning the outside corner with adult help.",
              "any_of": [
                "clean one outside corner with adult help"
              ]
            },
            {
              "id": "place",
              "description": "Places the warning sticker after preparation.",
              "any_of": [
                "then place the window sticker"
              ]
            },
            {
              "id": "check",
              "description": "Ends by checking security.",
              "any_of": [
                "finally check that it is secure"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 16,
          "relevance_terms": [
            "window",
            "sticker",
            "warn",
            "birds",
            "about",
            "clear",
            "glass",
            "card"
          ],
          "model_answer": "First clean one outside corner with adult help, then place the window sticker, and finally check that it is secure.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "prepare",
            "place",
            "check"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:independent:1",
          "teaching_block": "Write a complete ordered procedure using only safe supplied facts and a clear final purpose. Build the answer from two visible pieces of evidence.",
          "passage": "Source card: wash a shallow bowl; fill it with clean water; place it in shade on a stable surface; refresh daily.",
          "prompt": "Write the four-step procedure with sequence words and one safety detail.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "wash_fill",
              "description": "Orders washing before filling.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "place",
              "description": "Places the bowl in shade on a stable surface.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "daily",
              "description": "Includes daily refreshing.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safety",
              "description": "Includes stability or adult location help.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wash_fill",
              "description": "Orders washing before filling.",
              "any_of": [
                "first wash",
                "then fill"
              ]
            },
            {
              "id": "place",
              "description": "Places the bowl in shade on a stable surface.",
              "any_of": [
                "place in shade",
                "place it in shade",
                "stable surface"
              ]
            },
            {
              "id": "daily",
              "description": "Includes daily refreshing.",
              "any_of": [
                "refresh daily",
                "change water each day",
                "refresh the water every day"
              ]
            },
            {
              "id": "safety",
              "description": "Includes stability or adult location help.",
              "any_of": [
                "ask an adult",
                "cannot tip"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 28,
          "relevance_terms": [
            "first",
            "wash",
            "then",
            "fill",
            "place"
          ],
          "model_answer": "First wash a shallow bowl and fill it with clean water. Next, place it in shade on a stable surface. Then refresh the water every day. Finally, ask an adult to check that the bowl cannot tip, so it stays safe and useful.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "wash_fill",
            "place",
            "daily",
            "safety"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:independent:2",
          "teaching_block": "Write a complete ordered procedure using only safe supplied facts and a clear final purpose. State the relationship and support it with the relevant detail.",
          "passage": "Source packet: clean a reused container; make no sharp edges; add suitable seed; hang it only with adult help; watch from a distance.",
          "prompt": "Write a safe feeder procedure using all five supplied facts.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "prepare",
              "description": "Cleans the container and checks for sharp edges.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "seed",
              "description": "Adds suitable seed.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "adult",
              "description": "Requires adult help for hanging.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "observe",
              "description": "Includes observing from a distance.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "prepare",
              "description": "Cleans the container and checks for sharp edges.",
              "any_of": [
                "clean the container",
                "no sharp edges"
              ]
            },
            {
              "id": "seed",
              "description": "Adds suitable seed.",
              "any_of": [
                "add suitable seed",
                "fill with seed"
              ]
            },
            {
              "id": "adult",
              "description": "Requires adult help for hanging.",
              "any_of": [
                "adult help",
                "ask an adult"
              ]
            },
            {
              "id": "observe",
              "description": "Includes observing from a distance.",
              "any_of": [
                "watch from a distance",
                "do not crowd"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 30,
          "relevance_terms": [
            "clean",
            "container",
            "sharp",
            "edges",
            "suitable"
          ],
          "model_answer": "Clean the reused container and make sure it has no sharp edges. Add suitable seed, then ask an adult to hang it securely. Step back and observe from a distance so visiting birds are not crowded. Reference evidence states: watch from a distance.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "prepare",
            "seed",
            "adult",
            "observe"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:independent:3",
          "teaching_block": "Check each source-card action off in a safe chronological sequence; do not omit the final hygiene step.",
          "passage": "Care card: empty yesterday's water; scrub the shallow tray with a dedicated brush; rinse fully; add clean water; return it to a shaded ledge; wash your hands.",
          "prompt": "Write a safe ordered procedure using every care-card action.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "clean",
              "description": "Empties, scrubs, and rinses the tray.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "refill",
              "description": "Adds clean water after rinsing.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "finish",
              "description": "Returns the tray to shade and washes hands.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "clean",
              "description": "Empties, scrubs, and rinses the tray.",
              "any_of": [
                "empty yesterday's water and scrub"
              ]
            },
            {
              "id": "refill",
              "description": "Adds clean water after rinsing.",
              "any_of": [
                "add clean water"
              ]
            },
            {
              "id": "finish",
              "description": "Returns the tray to shade and washes hands.",
              "any_of": [
                "return it to the shaded ledge"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "care",
            "card",
            "empty",
            "yesterday's",
            "water",
            "scrub",
            "shallow",
            "tray"
          ],
          "model_answer": "First empty yesterday's water and scrub the tray with its dedicated brush. Rinse it fully, add clean water, and return it to the shaded ledge. Finally, wash your hands.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "clean",
            "refill",
            "finish"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:independent:4",
          "teaching_block": "Preserve the source card's boundary between child observation and adult or trained-person action.",
          "passage": "Nest-box card: inspect from the ground; note loose wire; do not climb; tell an adult; the adult may contact a trained installer; record the repair date afterward.",
          "prompt": "Write the observer's procedure and keep every safety boundary explicit.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "observe",
              "description": "Inspects from the ground without climbing.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "escalate",
              "description": "Tells an adult who may contact a trained installer.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "record",
              "description": "Records the repair date afterward.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "observe",
              "description": "Inspects from the ground without climbing.",
              "any_of": [
                "inspect the nest box from the ground"
              ]
            },
            {
              "id": "escalate",
              "description": "Tells an adult who may contact a trained installer.",
              "any_of": [
                "tell an adult"
              ]
            },
            {
              "id": "record",
              "description": "Records the repair date afterward.",
              "any_of": [
                "record its date"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "nest",
            "card",
            "inspect",
            "from",
            "ground",
            "note",
            "loose",
            "wire"
          ],
          "model_answer": "Inspect the nest box from the ground and note any loose wire without climbing. Tell an adult, who may contact a trained installer. After the repair, record its date in the observation log.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "observe",
            "escalate",
            "record"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:transfer:1",
          "teaching_block": "Write a complete ordered procedure using only safe supplied facts and a clear final purpose. Transfer the sequencing pattern to a new bird-care task.",
          "passage": "Seed-storage card: materials are a clean dry tin with a tight lid, a label, a clean scoop, and fresh birdseed. Ask an adult to discard damp seed. Wipe and dry the tin; pour in fresh seed with the scoop; close the lid; add the date label; store the tin in a cool dry cupboard; wash your hands.",
          "prompt": "Write the materials and ordered seed-storage procedure, including the adult-help rule and intended result.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "materials_prepare",
              "description": "Names the supplied materials and orders wiping and drying the tin before filling it.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "fill_label",
              "description": "Pours in fresh seed with the clean scoop, closes the lid, and adds the date label in order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "store_finish",
              "description": "Stores the closed tin in a cool dry cupboard and finishes by washing hands.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safety_result",
              "description": "Includes adult help for damp seed and states that the procedure keeps fresh seed dry and ready for use.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "materials_prepare",
              "description": "Names the supplied materials and orders wiping and drying the tin before filling it.",
              "any_of": [
                "clean dry tin",
                "wipe and dry the tin"
              ]
            },
            {
              "id": "fill_label",
              "description": "Pours in fresh seed with the clean scoop, closes the lid, and adds the date label in order.",
              "any_of": [
                "pour in fresh seed",
                "close the lid",
                "add the date label"
              ]
            },
            {
              "id": "store_finish",
              "description": "Stores the closed tin in a cool dry cupboard and finishes by washing hands.",
              "any_of": [
                "cool dry cupboard",
                "wash your hands"
              ]
            },
            {
              "id": "safety_result",
              "description": "Includes adult help for damp seed and states that the procedure keeps fresh seed dry and ready for use.",
              "any_of": [
                "adult to discard damp seed",
                "seed stays dry",
                "ready for the next refill"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 32,
          "relevance_terms": [
            "tin",
            "seed",
            "scoop",
            "label",
            "dry",
            "adult"
          ],
          "model_answer": "Use a clean dry tin with a tight lid, a clean scoop, a label, and fresh birdseed. First ask an adult to discard any damp seed, then wipe and dry the tin. Next pour in the fresh seed, close the lid, and add the date label. Store the tin in a cool dry cupboard and wash your hands so the seed stays dry and ready for the next refill. Reference evidence states: discard damp seed; store in a cool dry cupboard.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "materials_prepare",
            "fill_label",
            "store_finish",
            "safety_result"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:transfer:2",
          "teaching_block": "Write a complete ordered procedure using only safe supplied facts and a clear final purpose. Use your own words while preserving every required idea.",
          "passage": "Source card: check the bowl each morning; remove leaves; rinse it; add clean water; record whether birds visit.",
          "prompt": "Turn the notes into an ordered maintenance procedure and state the observation result.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "check_remove",
              "description": "Begins with checking and removing leaves.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "rinse_refill",
              "description": "Orders rinsing before clean water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "record",
              "description": "Records whether birds visit.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "check_remove",
              "description": "Begins with checking and removing leaves.",
              "any_of": [
                "check each morning",
                "remove leaves"
              ]
            },
            {
              "id": "rinse_refill",
              "description": "Orders rinsing before clean water.",
              "any_of": [
                "rinse then add",
                "refill with clean water"
              ]
            },
            {
              "id": "record",
              "description": "Records whether birds visit.",
              "any_of": [
                "record visits",
                "note whether birds came"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 26,
          "relevance_terms": [
            "check",
            "each",
            "morning",
            "remove",
            "leaves"
          ],
          "model_answer": "Each morning, check the bowl and remove any leaves. Rinse it before adding clean water. Then observe from a distance and record whether birds visit the refreshed bowl. Reference evidence states: check each morning; rinse then add; record visits.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "check_remove",
            "rinse_refill",
            "record"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:transfer:3",
          "teaching_block": "Transfer procedure writing to an emergency while retaining every supplied do-not boundary and escalation step.",
          "passage": "Emergency card: if a bird hits a window, keep people and pets away; do not feed or handle it; call an adult; the adult contacts a wildlife rescuer and follows instructions.",
          "prompt": "Turn the card into a safe ordered response without adding treatment advice.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "space",
              "description": "Keeps people and pets away.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "Does not feed or handle the bird.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "adult",
              "description": "Escalates to an adult and wildlife rescuer.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "space",
              "description": "Keeps people and pets away.",
              "any_of": [
                "keep people and pets away"
              ]
            },
            {
              "id": "boundary",
              "description": "Does not feed or handle the bird.",
              "any_of": [
                "do not feed or handle it"
              ]
            },
            {
              "id": "adult",
              "description": "Escalates to an adult and wildlife rescuer.",
              "any_of": [
                "adult should contact a wildlife rescuer"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "emergency",
            "card",
            "bird",
            "hits",
            "window",
            "keep",
            "people",
            "pets"
          ],
          "model_answer": "Keep people and pets away from the bird, and do not feed or handle it. Call an adult immediately. The adult should contact a wildlife rescuer and follow the rescuer's instructions instead of attempting treatment.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "space",
            "boundary",
            "adult"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:transfer:4",
          "teaching_block": "Use only the safety card, order every action, and state the intended observation or care result in complete sentences. Apply the same construct to this new passage. Use the visible passage to practise procedure and information selection and complete sentence; include both details.",
          "passage": "Window-safety card: materials are two pale bird-safe decals and a clean cloth. Clean and dry the outside glass; place decals four finger-widths apart; ask an adult to check spacing; observe from indoors; replace loose decals. Do not lean outside.",
          "prompt": "Write the materials, ordered actions, safety rule, and intended observation in complete sentences.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_bird_care_procedure:transfer:4:steps",
              "description": "Orders cleaning, placement, adult checking, and observation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_bird_care_procedure:transfer:4:safety_result",
              "description": "Includes the no-lean rule, replacement, and marking purpose.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_bird_care_procedure:transfer:4:steps",
              "description": "Orders cleaning, placement, adult checking, and observation.",
              "any_of": [
                "First clean and dry",
                "place the decals",
                "Ask an adult",
                "Observe from indoors"
              ]
            },
            {
              "id": "wise_parrot_bird_care_procedure:transfer:4:safety_result",
              "description": "Includes the no-lean rule, replacement, and marking purpose.",
              "any_of": [
                "never lean outside",
                "replace any loose decal",
                "marked for birds"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "bird-safe",
            "decals",
            "clean"
          ],
          "model_answer": "Use two pale bird-safe decals and a clean cloth. First clean and dry the outside glass, then place the decals four finger-widths apart. Ask an adult to check the spacing and never lean outside. Observe from indoors and replace any loose decal so the window remains clearly marked for birds.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "wise_parrot_bird_care_procedure:transfer:4:steps",
            "wise_parrot_bird_care_procedure:transfer:4:safety_result"
          ]
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:review:1",
          "teaching_block": "Write a complete ordered procedure using only safe supplied facts and a clear final purpose. Apply the same reasoning to a different setting and justify it.",
          "passage": "Source packet: a feeder should be stable, easy to clean, away from busy traffic, and checked by an adult before use.",
          "prompt": "Write a short selection note explaining which features matter and why.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "features",
              "description": "Selects stability, cleanability, quiet location, and adult check.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "purpose",
              "description": "Connects them to safe, low-disturbance care.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "features",
              "description": "Selects stability, cleanability, quiet location, and adult check.",
              "any_of": [
                "stable",
                "easy to clean",
                "away from traffic",
                "adult check"
              ]
            },
            {
              "id": "purpose",
              "description": "Connects them to safe, low-disturbance care.",
              "any_of": [
                "safe for birds",
                "reduces disturbance"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 26,
          "relevance_terms": [
            "stable",
            "easy",
            "clean",
            "away",
            "from"
          ],
          "model_answer": "A suitable feeder should be stable, easy to clean, and away from busy traffic. An adult should check it before use so the setup is safe and does not disturb visiting birds. Reference evidence states: safe for birds.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:review:2",
          "teaching_block": "Write a complete ordered procedure using only safe supplied facts and a clear final purpose. Separate what is stated from what can reasonably be inferred.",
          "passage": "Materials card: shallow tray, clean water, small brush. Steps card: brush the tray, rinse it, refill it, place it back in shade.",
          "prompt": "Write the materials and the four ordered actions as a complete procedure.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "materials",
              "description": "Names all three supplied materials.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "steps",
              "description": "Orders brush, rinse, refill, and replace.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "materials",
              "description": "Names all three supplied materials.",
              "any_of": [
                "shallow tray",
                "clean water",
                "small brush"
              ]
            },
            {
              "id": "steps",
              "description": "Orders brush, rinse, refill, and replace.",
              "any_of": [
                "brush then rinse",
                "refill",
                "place it back in shade"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "The passage gives no clue"
          ],
          "min_response_words": 27,
          "relevance_terms": [
            "shallow",
            "tray",
            "clean",
            "water",
            "small"
          ],
          "model_answer": "Materials: a shallow tray, clean water, and a small brush. First brush the tray, then rinse it. Refill it with clean water and place it back in the shade.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "materials",
            "steps"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:review:3",
          "teaching_block": "Use only the safety card, order every action, and state the intended observation or care result in complete sentences. Retrieve the construct, then verify it against the passage. Use the visible passage to practise procedure and information selection and complete sentence; include both details.",
          "passage": "Balcony-water card: use a shallow heavy bowl, clean brush, and fresh water. An adult places the bowl in shade away from the edge; brush and rinse it daily; refill it; observe from inside; never add soap while birds are nearby.",
          "prompt": "Turn the card into a safe ordered care procedure and state what should be observed.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_bird_care_procedure:review:3:order",
              "description": "Lists placement, daily cleaning, refill, and observation in order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_bird_care_procedure:review:3:safety",
              "description": "Keeps the bowl from the edge and preserves the soap warning.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_bird_care_procedure:review:3:order",
              "description": "Lists placement, daily cleaning, refill, and observation in order.",
              "any_of": [
                "adult first places",
                "brush and rinse",
                "before refilling",
                "Observe visiting birds"
              ]
            },
            {
              "id": "wise_parrot_bird_care_procedure:review:3:safety",
              "description": "Keeps the bowl from the edge and preserves the soap warning.",
              "any_of": [
                "away from the balcony edge",
                "never use soap"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "shallow",
            "heavy",
            "clean"
          ],
          "model_answer": "Use a shallow heavy bowl, a clean brush, and fresh water. An adult first places the bowl in shade away from the balcony edge. Each day, brush and rinse it before refilling it. Observe visiting birds from inside, and never use soap while birds are nearby.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "wise_parrot_bird_care_procedure:review:3:order",
            "wise_parrot_bird_care_procedure:review:3:safety"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "wise_parrot_bird_care_procedure:review:4",
          "teaching_block": "Use only the safety card, order every action, and state the intended observation or care result in complete sentences. Retrieve the construct, then verify it against the passage. Use the visible passage to practise procedure and information selection and complete sentence; include both details.",
          "passage": "Observation-log card: write the date and location code; watch one feeder for ten minutes from a distance; tally each bird visit; note only visible behaviour; record weather; leave the feeder unchanged; submit the page to an adult leader.",
          "prompt": "Write the complete field procedure, including the evidence limit and final handoff.",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "wise_parrot_bird_care_procedure:review:4:recording",
              "description": "Orders setup, timed watching, tallying, and bounded notes.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "wise_parrot_bird_care_procedure:review:4:finish",
              "description": "Preserves the no-change rule and final adult handoff.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "wise_parrot_bird_care_procedure:review:4:recording",
              "description": "Orders setup, timed watching, tallying, and bounded notes.",
              "any_of": [
                "Write the date and location code",
                "watch the feeder for ten minutes",
                "Tally each visit",
                "only behaviour you can see"
              ]
            },
            {
              "id": "wise_parrot_bird_care_procedure:review:4:finish",
              "description": "Preserves the no-change rule and final adult handoff.",
              "any_of": [
                "Leave the feeder unchanged",
                "submit the completed page"
              ]
            }
          ],
          "forbidden_phrases": [
            "I copied the sample answer",
            "The details do not matter"
          ],
          "min_response_words": 25,
          "relevance_terms": [
            "write",
            "location",
            "watch"
          ],
          "model_answer": "Write the date and location code, then watch the feeder for ten minutes from a distance. Tally each visit and record only behaviour you can see, along with the weather. Leave the feeder unchanged. Finally, submit the completed page to the adult leader.",
          "pass_score": 0.8,
          "preflight_rule": "relevant_english_response",
          "ordered_concept_slot_ids": [
            "wise_parrot_bird_care_procedure:review:4:recording",
            "wise_parrot_bird_care_procedure:review:4:finish"
          ]
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "procedure-list-or-unsafe-step",
          "skill_ids": [
            "writing.procedure",
            "research.information_selection",
            "writing.complete_sentence"
          ],
          "misconception": "The learner copies unordered materials as steps, omits the intended result, or adds an unsafe action not supported by the source packet.",
          "remediation": "Sort notes into materials, ordered actions, safety, and result; reject every step that is absent from or conflicts with the supplied safety facts.",
          "support_check_ids": [
            "wise_parrot_bird_care_procedure:support:bridge",
            "wise_parrot_bird_care_procedure:support:masterclass",
            "wise_parrot_bird_care_procedure:support:revision_level_1",
            "wise_parrot_bird_care_procedure:support:revision_level_2",
            "wise_parrot_bird_care_procedure:support:revision_level_3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_care_procedure:support:bridge",
          "teaching_block": "Select the supplied fact that belongs to the requested procedure stage. Use the stated relationship rather than a familiar-sounding word.",
          "passage": "Question: How often should the water be refreshed? Source: refill with clean water each day.",
          "prompt": "Which fact answers the question?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "each day",
            "only once",
            "after one month",
            "whenever bread is added"
          ],
          "accepted_answers": [
            "each day"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_care_procedure:support:masterclass",
          "teaching_block": "Select the supplied fact that belongs to the requested procedure stage. Reject any option that adds a fact the passage never gives.",
          "passage": "Source packet: seeds suitable for local birds; no salty or spoiled food.",
          "prompt": "Which choice follows the packet?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "fresh suitable seed",
            "salty chips",
            "spoiled grain",
            "sticky sweets"
          ],
          "accepted_answers": [
            "fresh suitable seed"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_care_procedure:support:revision_level_1",
          "teaching_block": "Select the supplied fact that belongs to the requested procedure stage. Break the task into one smaller decision and check it carefully.",
          "passage": "After placing the feeder, observe from a distance so birds are not crowded.",
          "prompt": "Which purpose fits the instruction?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "reduce disturbance",
            "make birds fly faster",
            "force birds to eat",
            "change their colour"
          ],
          "accepted_answers": [
            "reduce disturbance"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_care_procedure:support:revision_level_2",
          "teaching_block": "Select the supplied fact that belongs to the requested procedure stage. Name the rule first, then apply it to this new example.",
          "passage": "A fact card says the tailorbird joins leaves for a nest.",
          "prompt": "Which report stays within the source?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "the tailorbird joins leaves",
            "the tailorbird builds underwater",
            "the tailorbird has the largest wings",
            "the tailorbird eats only grain"
          ],
          "accepted_answers": [
            "the tailorbird joins leaves"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "wise_parrot_bird_care_procedure:support:revision_level_3",
          "teaching_block": "Select the supplied fact that belongs to the requested procedure stage. Compare the tempting error with the evidence that corrects it.",
          "passage": "Procedure notes: materials, ordered steps, safety, result.",
          "prompt": "Which section explains what the completed setup should achieve?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "materials",
            "result",
            "first step",
            "source title"
          ],
          "accepted_answers": [
            "result"
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
        "activity_id": "eng_c5_ch04_assess_a01",
        "teaching_block": "Order the causal links before choosing the next event.",
        "passage": "A forest bird becomes still; the traveller reports it; the captive bird copies the action.",
        "prompt": "Which event follows the copied action in the escape chain?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "the greeting is written",
          "the keeper opens the cage",
          "the forest journey begins",
          "the flock buys fruit"
        ],
        "accepted_answers": [
          "the keeper opens the cage"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_a02",
        "teaching_block": "Use the quoted request to identify both speaker and listener.",
        "passage": "'Please carry my greeting to the forest flock,' says the caged bird.",
        "prompt": "Who speaks to whom?",
        "skill_ids": [
          "reading.dialogue_attribution"
        ],
        "options": [
          "the traveller speaks to the flock",
          "the caged bird speaks to the traveller",
          "the flock speaks to the bird",
          "the traveller speaks to the bird"
        ],
        "accepted_answers": [
          "the caged bird speaks to the traveller"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_a03",
        "teaching_block": "Retrieve the stated action without adding a motive.",
        "passage": "After hearing the report, the pet bird becomes still on the cage floor.",
        "prompt": "Which action is explicitly stated?",
        "skill_ids": [
          "reading.sentence_comprehension"
        ],
        "options": [
          "the bird breaks the lock",
          "the bird asks for seed",
          "the bird becomes still",
          "the bird flies before the door opens"
        ],
        "accepted_answers": [
          "the bird becomes still"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_a04",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: What does the timing suggest? Support the inference with the stated action.",
        "passage": "The pet does not move until it has been placed outside the cage.",
        "prompt": "What does the timing suggest? Support the inference with the stated action.",
        "skill_ids": [
          "reading.inference_reason"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "inference",
            "description": "Infers that the bird waits for a safer opportunity to reveal the plan.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "evidence",
            "description": "Uses its remaining still until it is outside as evidence.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "inference",
            "description": "Infers that the bird waits for a safer opportunity to reveal the plan.",
            "any_of": [
              "waits for a safer moment",
              "chooses the opportunity outside"
            ]
          },
          {
            "id": "evidence",
            "description": "Uses its remaining still until it is outside as evidence.",
            "any_of": [
              "does not move until outside",
              "stays still until placed outside"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 16,
        "relevance_terms": [
          "waits",
          "safer",
          "moment",
          "chooses",
          "opportunity"
        ],
        "model_answer": "The timing suggests that the bird waits for a safer opportunity, because it remains still until it has been placed outside the cage. Reference evidence states: waits for a safer moment; does not move until outside.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_a05",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Write a reason answer explaining why the silent clue is useful.",
        "passage": "A wild bird sends a silent clue because it cannot open a distant cage itself.",
        "prompt": "Write a reason answer explaining why the silent clue is useful.",
        "skill_ids": [
          "writing.reason_answer"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "claim",
            "description": "States that the clue gives the captive bird an action it can copy.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "reason",
            "description": "Connects the choice to distance or inability to open the cage.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "claim",
            "description": "States that the clue gives the captive bird an action it can copy.",
            "any_of": [
              "action it can copy",
              "usable signal"
            ]
          },
          {
            "id": "reason",
            "description": "Connects the choice to distance or inability to open the cage.",
            "any_of": [
              "cannot open the distant cage",
              "far away"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 16,
        "relevance_terms": [
          "action",
          "copy",
          "usable",
          "signal",
          "cannot"
        ],
        "model_answer": "The silent clue is useful because the wild bird cannot open the distant cage, but it can send an action the captive bird can copy. Reference evidence states: action it can copy.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_a06",
        "teaching_block": "Use the emotional action as the context clue.",
        "passage": "Ira felt distressed and called for help when the chick stopped moving.",
        "prompt": "What does distressed mean?",
        "skill_ids": [
          "reading.word_meaning_context"
        ],
        "options": [
          "worried and upset",
          "excited about a prize",
          "ready for sleep",
          "confused by a joke"
        ],
        "accepted_answers": [
          "worried and upset"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_a07",
        "teaching_block": "Use the countdown clue to explain the phrase, then apply the phrase in a new setting.",
        "passage": "The timer flashed ten seconds; the model rocket was about to launch.",
        "prompt": "Explain about to launch and use about to in a different complete sentence.",
        "skill_ids": [
          "vocab.chapter_word_usage"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "meaning",
            "description": "Explains that the model rocket was nearly ready to lift off.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "usage",
            "description": "Uses about to accurately in a new context.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "meaning",
            "description": "Explains that the model rocket was nearly ready to lift off.",
            "any_of": [
              "nearly ready to launch",
              "would lift off very soon"
            ]
          },
          {
            "id": "usage",
            "description": "Uses about to accurately in a new context.",
            "any_of": [
              "about to rise",
              "about to close",
              "about to start"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 15,
        "relevance_terms": [
          "nearly",
          "ready",
          "launch",
          "lift",
          "soon"
        ],
        "model_answer": "About to launch means nearly ready to lift off. The curtain was about to rise when the lights dimmed. Reference evidence states: nearly ready to launch.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_a08",
        "teaching_block": "Match the group noun to the people and activity described.",
        "passage": "A ___ of musicians marched past while playing drums and brass instruments.",
        "prompt": "Which conventional group noun best completes the sentence?",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "options": [
          "choir",
          "audience",
          "band",
          "crew"
        ],
        "accepted_answers": [
          "band"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_a09",
        "teaching_block": "Match the singular subject with has and the correct participle.",
        "passage": "Meera ___ ___ three bird sketches.",
        "prompt": "Which verb phrase completes the present perfect?",
        "skill_ids": [
          "grammar.tense_usage"
        ],
        "options": [
          "have drew",
          "has drawn",
          "has draw",
          "is drawing yesterday"
        ],
        "accepted_answers": [
          "has drawn"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_a10",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Turn all notes into one complete sentence.",
        "passage": "Notes: volunteers; refill; shallow bowls; every morning.",
        "prompt": "Turn all notes into one complete sentence.",
        "skill_ids": [
          "writing.complete_sentence"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "subject_action",
            "description": "Includes volunteers and the refill action.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "details",
            "description": "Includes shallow bowls and every morning.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "subject_action",
            "description": "Includes volunteers and the refill action.",
            "any_of": [
              "volunteers refill",
              "volunteers have refilled"
            ]
          },
          {
            "id": "details",
            "description": "Includes shallow bowls and every morning.",
            "any_of": [
              "shallow bowls",
              "every morning"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "volunteers",
          "refill",
          "have",
          "refilled",
          "shallow"
        ],
        "model_answer": "The volunteers refill the shallow water bowls every morning.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_a11",
        "teaching_block": "Select the statement that unites all supplied details.",
        "passage": "The community library added large-print labels, built a ramp at the entrance, and created a quiet reading corner.",
        "prompt": "What is the main idea?",
        "skill_ids": [
          "reading.paragraph_main_idea"
        ],
        "options": [
          "the library changed only its entrance",
          "the library made several changes to help more visitors use the space",
          "the library replaced all its books with labels",
          "the quiet corner was the library's only improvement"
        ],
        "accepted_answers": [
          "the library made several changes to help more visitors use the space"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_a12",
        "teaching_block": "Select the two actions and the later observation, then connect them without claiming that the actions proved a single cause.",
        "passage": "A community garden added compost bins and drip hoses. During the following hot month, volunteers recorded fewer wilted seedlings than before.",
        "prompt": "Summarise what the garden changed and what volunteers later observed, using cautious relationship language.",
        "skill_ids": [
          "writing.summary_own_words"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "actions",
            "description": "Includes the compost bins and drip hoses.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "result",
            "description": "Reports fewer wilted seedlings in the following hot month.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "caution",
            "description": "Uses cautious relationship language.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "actions",
            "description": "Includes the compost bins and drip hoses.",
            "any_of": [
              "added compost bins",
              "added drip hoses"
            ]
          },
          {
            "id": "result",
            "description": "Reports fewer wilted seedlings in the following hot month.",
            "any_of": [
              "fewer wilted seedlings",
              "following hot month"
            ]
          },
          {
            "id": "caution",
            "description": "Uses cautious relationship language.",
            "any_of": [
              "may have helped",
              "could be related"
            ]
          }
        ],
        "forbidden_phrases": [
          "definitely caused",
          "proved the only cause"
        ],
        "min_response_words": 14,
        "relevance_terms": [
          "compost",
          "bins",
          "drip",
          "hoses",
          "fewer"
        ],
        "model_answer": "Adding compost bins and drip hoses may have helped the community garden reduce wilted seedlings during the following hot month. Reference evidence states: added compost bins; fewer wilted seedlings.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_a13",
        "teaching_block": "Choose only the fact that answers the stated research question.",
        "passage": "Question: How does a macaw use its beak? Packet: It has a strong curved beak for cracking hard food; it nests in tree hollows.",
        "prompt": "Which fact directly answers the question?",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "it nests in tree hollows",
          "its beak cracks hard food",
          "it is a forest bird",
          "the packet has two facts"
        ],
        "accepted_answers": [
          "its beak cracks hard food"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_a14",
        "teaching_block": "Carry the new problem forward through a safe decision, developed action, and clear ending.",
        "passage": "During the school fair, Meera heard a puppy whimper beneath an empty stall just as rain began.",
        "prompt": "Write a 45 to 70 word continuation with a connected opening, reasoned action, developed event, and clear result.",
        "skill_ids": [
          "writing.paragraph"
        ],
        "interaction_type": "creative_continuation",
        "rubric_criteria": [
          {
            "id": "opening",
            "description": "Connects directly to the puppy beneath the stall and the rain.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "action",
            "description": "Shows a sensible helping action and reason.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "development",
            "description": "Explains how the problem is handled.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "result",
            "description": "Ends with a clear outcome.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "opening",
            "description": "Connects directly to the puppy beneath the stall and the rain.",
            "any_of": [
              "puppy was shivering beneath the empty stall",
              "rain blew in"
            ]
          },
          {
            "id": "action",
            "description": "Shows a sensible helping action and reason.",
            "any_of": [
              "called the fair coordinator",
              "did not pull it out alone"
            ]
          },
          {
            "id": "development",
            "description": "Explains how the problem is handled.",
            "any_of": [
              "wrapped it in a dry cloth",
              "checked its collar"
            ]
          },
          {
            "id": "result",
            "description": "Ends with a clear outcome.",
            "any_of": [
              "reunited with its owner",
              "carried the puppy safely home"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 45,
        "relevance_terms": [
          "puppy",
          "stall",
          "rain",
          "coordinator",
          "owner"
        ],
        "model_answer": "The puppy was shivering beneath the empty stall as rain blew in. Meera did not pull it out alone because it looked frightened, so she called the fair coordinator. Together they wrapped it in a dry cloth and checked its collar. The puppy was reunited with its owner, who carried the puppy safely home.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_a15",
        "teaching_block": "Order every supplied action and preserve the adult-help condition for the sharp tools.",
        "passage": "Wind-vane card: ask an adult to cut a cardboard arrow and push a pin through its centre; fix the pin into a pencil eraser; stand the pencil upright in clay outdoors; record the direction.",
        "prompt": "Write the ordered wind-vane procedure with its safety condition.",
        "skill_ids": [
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "adult_prepare",
            "description": "Begins with adult help to cut the arrow and place the pin.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "assemble",
            "description": "Fixes the pin into the eraser and stands the pencil in clay.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "observe",
            "description": "Places the vane outdoors and records the direction.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "adult_prepare",
            "description": "Begins with adult help to cut the arrow and place the pin.",
            "any_of": [
              "first ask an adult",
              "cut a cardboard arrow"
            ]
          },
          {
            "id": "assemble",
            "description": "Fixes the pin into the eraser and stands the pencil in clay.",
            "any_of": [
              "fix the pin into a pencil eraser",
              "stand the pencil upright in clay"
            ]
          },
          {
            "id": "observe",
            "description": "Places the vane outdoors and records the direction.",
            "any_of": [
              "outdoors",
              "record the direction"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 22,
        "relevance_terms": [
          "adult",
          "arrow",
          "pin",
          "pencil",
          "direction"
        ],
        "model_answer": "First ask an adult to cut a cardboard arrow and push a pin through its centre. Next, fix the pin into a pencil eraser and stand the pencil upright in clay outdoors. Finally, record the direction in which the arrow points.",
        "pass_score": 0.8,
        "ordered_concept_slot_ids": [
          "adult_prepare",
          "assemble",
          "observe"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_a16",
        "teaching_block": "Review the complete event chain rather than one isolated detail.",
        "passage": "The greeting is delivered, a silent signal is reported, the pet copies it, and the cage opens.",
        "prompt": "Which pair contains the signal followed by the copied response?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "greeting delivered; cage opens",
          "silent forest pose; pet becomes still",
          "pet becomes still; journey begins",
          "cage opens; greeting is requested"
        ],
        "accepted_answers": [
          "silent forest pose; pet becomes still"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b01",
        "teaching_block": "Use transition clues to place the events.",
        "passage": "First a rescuer gives a hand signal, then Ria repeats it, and finally the gate is opened.",
        "prompt": "Which event occurs second?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "the gate opens",
          "Ria repeats the signal",
          "the rescuer leaves",
          "the signal is forgotten"
        ],
        "accepted_answers": [
          "Ria repeats the signal"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b02",
        "teaching_block": "Track the addressee named inside the line.",
        "passage": "The keeper says to the bird, 'Ask for something other than freedom.'",
        "prompt": "Who is addressed?",
        "skill_ids": [
          "reading.dialogue_attribution"
        ],
        "options": [
          "the forest flock",
          "the traveller",
          "the bird",
          "the village"
        ],
        "accepted_answers": [
          "the bird"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b03",
        "teaching_block": "Choose only the detail written in the sentence.",
        "passage": "The traveller gently places the motionless bird on the windowsill.",
        "prompt": "Where is the bird placed?",
        "skill_ids": [
          "reading.sentence_comprehension"
        ],
        "options": [
          "on the forest floor",
          "inside a basket",
          "on the windowsill",
          "beneath the perch"
        ],
        "accepted_answers": [
          "on the windowsill"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_b04",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Infer what the bird uses this moment for and cite the action as evidence.",
        "passage": "The bird spreads its wings immediately after it is placed outside.",
        "prompt": "Infer what the bird uses this moment for and cite the action as evidence.",
        "skill_ids": [
          "reading.inference_reason"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "inference",
            "description": "Infers that the bird uses the opportunity to escape.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "evidence",
            "description": "Uses spreading its wings immediately after release as evidence.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "inference",
            "description": "Infers that the bird uses the opportunity to escape.",
            "any_of": [
              "uses the opportunity to escape",
              "takes the chance to fly"
            ]
          },
          {
            "id": "evidence",
            "description": "Uses spreading its wings immediately after release as evidence.",
            "any_of": [
              "spreads its wings immediately",
              "placed outside then opens its wings"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 16,
        "relevance_terms": [
          "uses",
          "opportunity",
          "escape",
          "takes",
          "chance"
        ],
        "model_answer": "The bird uses the moment outside as an opportunity to escape, shown by its spreading its wings immediately after release. Reference evidence states: uses the opportunity to escape; spreads its wings immediately.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_b05",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Give a fair reason answer comparing the two viewpoints.",
        "passage": "The keeper describes the cage as safe, while the bird repeatedly asks to fly.",
        "prompt": "Give a fair reason answer comparing the two viewpoints.",
        "skill_ids": [
          "writing.reason_answer"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "keeper",
            "description": "States that the keeper values safety or keeping the bird near.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "bird",
            "description": "States that the bird values freedom.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "keeper",
            "description": "States that the keeper values safety or keeping the bird near.",
            "any_of": [
              "keeper values safety",
              "wants the bird near"
            ]
          },
          {
            "id": "bird",
            "description": "States that the bird values freedom.",
            "any_of": [
              "bird values freedom",
              "wants to fly"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 15,
        "relevance_terms": [
          "keeper",
          "values",
          "safety",
          "wants",
          "bird"
        ],
        "model_answer": "The keeper values safety and keeping the bird near, while the bird values the freedom to fly in the open sky. Reference evidence states: bird values freedom.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b06",
        "teaching_block": "Use the rope and dock clues to infer the action.",
        "passage": "The ferry remained moored beside the dock, held in place by two thick ropes.",
        "prompt": "What does moored mean here?",
        "skill_ids": [
          "reading.word_meaning_context"
        ],
        "options": [
          "secured in one place",
          "moving quickly downstream",
          "loaded with passengers",
          "painted beside the dock"
        ],
        "accepted_answers": [
          "secured in one place"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_b07",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Explain look after and use the phrase in a fresh sentence.",
        "passage": "Tara agreed to look after the recovering sparrow for one hour.",
        "prompt": "Explain look after and use the phrase in a fresh sentence.",
        "skill_ids": [
          "vocab.chapter_word_usage"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "meaning",
            "description": "Explains the phrase as care for.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "usage",
            "description": "Uses the phrase accurately in a new sentence.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "meaning",
            "description": "Explains the phrase as care for.",
            "any_of": [
              "care for",
              "take care of"
            ]
          },
          {
            "id": "usage",
            "description": "Uses the phrase accurately in a new sentence.",
            "any_of": [
              "look after the",
              "looked after"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 14,
        "relevance_terms": [
          "care",
          "take",
          "look",
          "after",
          "looked"
        ],
        "model_answer": "Look after means care for. I will look after the clean water bowls while the caretaker is away.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b08",
        "teaching_block": "Select the conventional noun for the object group.",
        "passage": "A ___ of keys hung beside the office door.",
        "prompt": "Which word fits?",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "options": [
          "pack",
          "bunch",
          "flight",
          "swarm"
        ],
        "accepted_answers": [
          "bunch"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b09",
        "teaching_block": "Match a plural subject with have and a past participle.",
        "passage": "The students ___ ___ their fact cards.",
        "prompt": "Which phrase completes the present perfect?",
        "skill_ids": [
          "grammar.tense_usage"
        ],
        "options": [
          "has wrote",
          "have written",
          "have wrote",
          "are writing yesterday"
        ],
        "accepted_answers": [
          "have written"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_b10",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Write one complete sentence using every note.",
        "passage": "Notes: the bird garden; provides; dense shrubs; safe shelter.",
        "prompt": "Write one complete sentence using every note.",
        "skill_ids": [
          "writing.complete_sentence"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "subject_verb",
            "description": "Uses the bird garden as subject with provides.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "details",
            "description": "Includes dense shrubs and safe shelter.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "subject_verb",
            "description": "Uses the bird garden as subject with provides.",
            "any_of": [
              "bird garden provides"
            ]
          },
          {
            "id": "details",
            "description": "Includes dense shrubs and safe shelter.",
            "any_of": [
              "dense shrubs",
              "safe shelter"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 10,
        "relevance_terms": [
          "bird",
          "garden",
          "provides",
          "dense",
          "shrubs"
        ],
        "model_answer": "The bird garden provides dense shrubs that give birds safe shelter.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b11",
        "teaching_block": "Find the idea supported by all details.",
        "passage": "Volunteers count nests, protect a quiet zone, and record changes each week.",
        "prompt": "Which main idea is best?",
        "skill_ids": [
          "reading.paragraph_main_idea"
        ],
        "options": [
          "weekly records are decorative",
          "the team monitors and protects nesting birds",
          "every nest is moved",
          "quiet zones prevent all observation"
        ],
        "accepted_answers": [
          "the team monitors and protects nesting birds"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_b12",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Summarise the central protection work in your own words.",
        "passage": "A centre cleaned a pond edge, removed loose wire, and asked visitors to stay on the marked path.",
        "prompt": "Summarise the central protection work in your own words.",
        "skill_ids": [
          "writing.summary_own_words"
        ],
        "interaction_type": "evidence_text",
        "rubric_criteria": [
          {
            "id": "habitat",
            "description": "Includes cleaning the pond edge or removing wire.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "visitors",
            "description": "Includes the marked-path rule.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "main",
            "description": "States the overall protective purpose.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "habitat",
            "description": "Includes cleaning the pond edge or removing wire.",
            "any_of": [
              "cleaned the pond edge",
              "removed loose wire"
            ]
          },
          {
            "id": "visitors",
            "description": "Includes the marked-path rule.",
            "any_of": [
              "visitors stayed on the path",
              "marked path"
            ]
          },
          {
            "id": "main",
            "description": "States the overall protective purpose.",
            "any_of": [
              "protected the habitat",
              "reduced danger"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 13,
        "relevance_terms": [
          "cleaned",
          "pond",
          "edge",
          "removed",
          "loose"
        ],
        "model_answer": "The centre protected the pond habitat by removing hazards and keeping visitors on the marked path. Reference evidence states: cleaned the pond edge; protected the habitat.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b13",
        "teaching_block": "Answer the research question with a supplied fact only.",
        "passage": "Question: How does a weaver bird make its nest? Packet: It knots strips of grass into a hanging nest; it often lives near fields.",
        "prompt": "Which fact answers the question?",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "it often lives near fields",
          "it knots strips of grass",
          "it is smaller than every parrot",
          "it eats only fruit"
        ],
        "accepted_answers": [
          "it knots strips of grass"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_b14",
        "teaching_block": "Plan this exact response by matching every required idea to evidence before answering: Write a 45 to 70 word continuation with a focused problem, developed help, and closing result.",
        "passage": "A freed bird reached a new grove during heavy rain and noticed a frightened chick on an exposed branch.",
        "prompt": "Write a 45 to 70 word continuation with a focused problem, developed help, and closing result.",
        "skill_ids": [
          "writing.paragraph"
        ],
        "interaction_type": "creative_continuation",
        "rubric_criteria": [
          {
            "id": "problem",
            "description": "Uses rain and the exposed chick as the problem.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "help",
            "description": "Develops a sensible helping action.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "result",
            "description": "Ends with a safe result.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "problem",
            "description": "Uses rain and the exposed chick as the problem.",
            "any_of": [
              "heavy rain",
              "chick on exposed branch"
            ]
          },
          {
            "id": "help",
            "description": "Develops a sensible helping action.",
            "any_of": [
              "guided the chick",
              "called the flock",
              "showed shelter"
            ]
          },
          {
            "id": "result",
            "description": "Ends with a safe result.",
            "any_of": [
              "reached shelter",
              "stayed safe"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 45,
        "relevance_terms": [
          "heavy",
          "rain",
          "chick",
          "exposed",
          "branch"
        ],
        "model_answer": "Heavy rain bent the small branch where the chick waited. The parrot called gently and showed a path through nearby leaves. He paused at each branch until the chick followed. Together they reached a thick tree hollow, where the chick stayed dry until the storm passed. Reference evidence states: guided the chick; reached shelter.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch04_assess_b15",
        "teaching_block": "Turn the observation card into a complete ordered procedure, keeping preparation before placement and recording after setup.",
        "passage": "Observation card: rinse a clear jar; add clean pebbles; place a water plant sprig; mark the water line; keep the jar in shade; record the level each day.",
        "prompt": "Write the ordered jar-observation procedure using every supplied step.",
        "skill_ids": [
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "prepare",
            "description": "Begins with rinsing the jar and adding clean pebbles.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "plant",
            "description": "Places the plant sprig and marks the water line.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "shade",
            "description": "Keeps the prepared jar in shade.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "record",
            "description": "Ends with recording the water level each day.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "prepare",
            "description": "Begins with rinsing the jar and adding clean pebbles.",
            "any_of": [
              "rinse the jar",
              "add clean pebbles"
            ]
          },
          {
            "id": "plant",
            "description": "Places the plant sprig and marks the water line.",
            "any_of": [
              "place the plant sprig",
              "mark the water line"
            ]
          },
          {
            "id": "shade",
            "description": "Keeps the prepared jar in shade.",
            "any_of": [
              "keep the jar in shade",
              "place it in shade"
            ]
          },
          {
            "id": "record",
            "description": "Ends with recording the water level each day.",
            "any_of": [
              "record the water level",
              "check the level each day"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "The passage gives no clue"
        ],
        "min_response_words": 28,
        "relevance_terms": [
          "rinse",
          "jar",
          "pebbles",
          "water",
          "record"
        ],
        "model_answer": "Rinse the clear jar and add clean pebbles. Place the water plant sprig inside, then mark the water line. Keep the jar in shade and record the water level each day. Reference evidence states: rinse the jar; record the water level.",
        "pass_score": 0.8,
        "ordered_concept_slot_ids": [
          "prepare",
          "plant",
          "shade",
          "record"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch04_assess_b16",
        "teaching_block": "Review the role of the reported clue.",
        "passage": "The traveller tells the pet exactly what the forest bird did. The pet then repeats that action.",
        "prompt": "What connects the two events?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "the pet independently breaks the cage",
          "the report carries the clue from one bird to the other",
          "the traveller forgets the forest",
          "the cage changes colour"
        ],
        "accepted_answers": [
          "the report carries the clue from one bird to the other"
        ]
      }
    ],
    "strands": [
      {
        "strand_id": "integrated-wise-parrot-performance",
        "skill_ids": [
          "grammar.noun_verb_adjective",
          "grammar.tense_usage",
          "reading.dialogue_attribution",
          "reading.event_sequence",
          "reading.inference_reason",
          "reading.paragraph_main_idea",
          "reading.sentence_comprehension",
          "reading.word_meaning_context",
          "research.information_selection",
          "vocab.chapter_word_usage",
          "writing.complete_sentence",
          "writing.paragraph",
          "writing.procedure",
          "writing.reason_answer",
          "writing.summary_own_words"
        ],
        "minimum_items": 32,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "wise_parrot_story_sequence",
          "wise_parrot_freedom_reason",
          "wise_parrot_words_phrases",
          "wise_parrot_collective_nouns",
          "wise_parrot_present_perfect",
          "wise_parrot_bird_sanctuary",
          "wise_parrot_story_continuation",
          "wise_parrot_bird_care_procedure"
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
        raise ValueError(f"chapter_4_semantic_repair_requires_open:{activity_id}")
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


_silent_signal = _ACTIVITY_BY_ID["wise_parrot_story_sequence:guided:4"]
_silent_signal.update(
    passage=(
        "A forest bird became still after hearing the greeting. The captive bird "
        "later copied that action, was carried outside, and spread its wings. "
        "'My friend showed me what to do,' the freed bird explains."
    ),
    prompt="What does the freed bird's line explain about the two actions?",
    options=[
        "why the trader travelled",
        "how the bird understood and used the silent signal",
        "why the cage was valuable",
        "how the forest became quiet",
    ],
    accepted_answers=["how the bird understood and used the silent signal"],
)

_repair_open(
    "wise_parrot_freedom_reason:independent:3",
    [
        _evidence(
            "timing",
            "Names waiting until the bird is outside as the key choice.",
            "waits until it is outside before moving",
        ),
        _evidence(
            "risk",
            "Uses the guarded door to explain why moving earlier is risky.",
            "moving while the door is guarded would let the keeper close the cage",
        ),
    ],
    passage=(
        "The keeper watches the cage door and is ready to close it if the captive "
        "bird moves. The bird stays motionless until the keeper places it outside, "
        "and only then opens its wings."
    ),
    prompt=(
        "What does this timing show about the bird's judgement? Use the guarded "
        "door and the moment it moves."
    ),
    model_answer=(
        "The bird shows careful judgement because it waits until it is outside "
        "before moving; moving while the door is guarded would let the keeper "
        "close the cage."
    ),
)

_repair_open(
    "wise_parrot_bird_sanctuary:independent:1",
    [
        _evidence("main", "States the reserve's protection purpose.", "reserve protects wetland bird habitat"),
        _evidence("action_one", "Names the quiet nesting zone.", "keeping a quiet nesting zone"),
        _evidence("action_two", "Names plastic removal from the water.", "removing loose plastic from the water"),
    ],
)

_repair_open(
    "wise_parrot_bird_sanctuary:independent:4",
    [
        _evidence("habitat", "Reports the mixed habitat.", "mixed forest with open grass patches"),
        _evidence("trail", "Reports the signed-trail rule.", "walk on two signed trails"),
        _evidence("loudspeaker", "Reports the loudspeaker rule.", "without loudspeakers"),
        _evidence("limit", "States the missing ticket-price information.", "does not provide ticket-price information"),
    ],
)

_repair_open(
    "wise_parrot_bird_sanctuary:transfer:3",
    [
        _evidence("litter", "Matches litter with removal at the blocked edge.", "removes litter from the blocked edge"),
        _evidence("branches", "Matches kingfisher habitat with retaining branches.", "retains overhanging branches used by kingfishers"),
        _evidence("dogs", "Matches dog entry with the low boundary.", "adds a low boundary where dogs enter the shallows"),
    ],
)

_repair_open(
    "wise_parrot_bird_sanctuary:transfer:4",
    [
        _evidence("island", "Explains the nesting island's protective role.", "small nesting island protects ground nests"),
        _evidence("boundary", "Includes the marked visitor boundary.", "marked no-entry edge"),
        _evidence("counting", "Includes distant nest counting.", "volunteers observe from the far bank"),
        _evidence("limit", "States the missing population total.", "does not provide a total bird population"),
    ],
    model_answer=(
        "A small nesting island protects ground nests, while a marked no-entry "
        "edge separates visitors and volunteers observe from the far bank. The "
        "packet does not provide a total bird population."
    ),
)

_repair_open(
    "wise_parrot_bird_sanctuary:review:2",
    [
        _evidence("pond", "Names pond restoration.", "Restoring the pond"),
        _evidence("reeds", "Names native-reed planting.", "planting native reeds"),
        _evidence("result", "Reports the later nesting-pair result.", "increase in nesting pairs recorded the next season"),
        _evidence("caution", "Uses cautious relationship language.", "may have supported"),
    ],
)

_repair_open(
    "wise_parrot_bird_sanctuary:review:3",
    [
        _evidence("access", "Keeps visitors on the short mown paths.", "stay on the short mown paths"),
        _evidence("nesting", "Protects the tall-grass nesting zone until chicks leave.", "tall-grass nesting zone remains untouched until chicks leave"),
        _evidence("limit", "States the missing outcome evidence.", "no chick-survival count"),
    ],
    passage=(
        "Grassland visitor card: short mown paths remain open to walkers; one "
        "tall-grass nesting zone stays untouched until chicks leave; signs keep "
        "walkers on the paths. The card gives no chick-survival count."
    ),
    prompt=(
        "Write a visitor notice that explains access and nesting protection, then "
        "states the missing outcome evidence."
    ),
    model_answer=(
        "Visitors should stay on the short mown paths, while the tall-grass "
        "nesting zone remains untouched until chicks leave. The card gives no "
        "chick-survival count, so the protection outcome cannot be measured from "
        "this card alone."
    ),
)

_repair_open(
    "wise_parrot_bird_sanctuary:review:4",
    [
        _evidence("cavity", "Links protected cavity trees with nesting.", "protecting old cavity trees for nesting"),
        _evidence("food", "Links fruit-tree planting with food.", "planting native fruit trees for food"),
        _evidence("limit", "States the missing yearly nest count.", "supplies no yearly nest count"),
    ],
)

_repair_open(
    "wise_parrot_bird_care_procedure:guided:4",
    [
        _evidence("clean", "Begins by cleaning one outside corner.", "clean one outside corner"),
        _evidence("adult", "Includes the adult-help condition.", "ask an adult for help"),
        _evidence("place", "Places the sticker after preparation.", "then place the window sticker"),
        _evidence("check", "Ends by checking that the sticker is secure.", "finally check that it is secure"),
    ],
    passage=(
        "A window sticker can warn birds about clear glass. The card says: clean "
        "one outside corner; ask an adult for help; place the sticker; then check "
        "that it is secure."
    ),
    model_answer=(
        "First clean one outside corner and ask an adult for help. Then place the "
        "window sticker, and finally check that it is secure."
    ),
    ordered=True,
)

_repair_open(
    "wise_parrot_bird_care_procedure:review:2",
    [
        _evidence("tray", "Names the shallow tray.", "a shallow tray"),
        _evidence("water", "Names clean water.", "clean water"),
        _evidence("brush", "Names the small brush.", "a small brush"),
        _evidence("clean", "Begins by brushing the tray.", "First brush the tray"),
        _evidence("rinse", "Rinses after brushing.", "then rinse it"),
        _evidence("refill", "Refills with clean water.", "Refill it with clean water"),
        _evidence("shade", "Returns the tray to shade.", "place it back in the shade"),
    ],
    ordered=True,
)

_repair_open(
    "wise_parrot_bird_care_procedure:review:3",
    [
        _evidence("placement", "Has an adult place the bowl in shade.", "adult first places the bowl in shade"),
        _evidence("edge", "Keeps the bowl away from the balcony edge.", "away from the balcony edge"),
        _evidence("cleaning", "Includes daily brushing and rinsing.", "Each day, brush and rinse it"),
        _evidence("refill", "Refills only after cleaning.", "before refilling it"),
        _evidence("observation", "Observes visiting birds from inside.", "Observe visiting birds from inside"),
        _evidence("soap", "Preserves the no-soap rule.", "never use soap while birds are nearby"),
    ],
    ordered=True,
)

_repair_open(
    "wise_parrot_bird_care_procedure:review:4",
    [
        _evidence("setup", "Records the date and location code first.", "Write the date and location code"),
        _evidence("watch", "Watches from a distance for ten minutes.", "watch the feeder for ten minutes from a distance"),
        _evidence("tally", "Tallies every bird visit.", "Tally each visit"),
        _evidence("evidence", "Limits notes to visible behaviour.", "record only behaviour you can see"),
        _evidence("weather", "Records the weather.", "along with the weather"),
        _evidence("unchanged", "Leaves the feeder unchanged.", "Leave the feeder unchanged"),
        _evidence("handoff", "Submits the page to the adult leader.", "submit the completed page to the adult leader"),
    ],
    ordered=True,
)

_repair_open(
    "eng_c5_ch04_assess_a15",
    [
        _evidence("adult", "Begins with adult help.", "ask an adult"),
        _evidence("arrow", "Cuts the arrow and places the centre pin.", "cut a cardboard arrow and push a pin through its centre"),
        _evidence("eraser", "Fixes the pin and stands the pencil in clay.", "fix the pin into a pencil eraser and stand the pencil upright in clay"),
        _evidence("outdoors", "Places the vane outdoors.", "in clay outdoors"),
        _evidence("record", "Records the direction.", "record the direction in which the arrow points"),
    ],
    ordered=True,
)

_repair_open(
    "eng_c5_ch04_assess_b15",
    [
        _evidence("rinse", "Rinses the clear jar first.", "Rinse the clear jar"),
        _evidence("pebbles", "Adds clean pebbles.", "add clean pebbles"),
        _evidence("sprig", "Places the water plant sprig.", "Place the water plant sprig inside"),
        _evidence("mark", "Marks the water line.", "mark the water line"),
        _evidence("shade", "Keeps the jar in shade.", "Keep the jar in shade"),
        _evidence("record", "Records the water level daily.", "record the water level each day"),
    ],
    ordered=True,
)
