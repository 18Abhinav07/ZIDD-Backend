"""Authored deep manifest for Class 5 English Chapter 6.

The embedded baseline preserves the original Zidd-authored chapter manifest.
The source-level expansion below supplies the strengthened deep-loop pools and
fresh misconception support used by the generic chapter compiler.
"""

from __future__ import annotations

import json

from app.content.school_rebuild_manifests.english.class_5.eng_c5_ch02 import (
    _evidence,
    _open_activity,
    _task,
)


MANIFEST = json.loads(r'''{
  "schema_version": "school-class5-deep-manifest-v1",
  "chapter": {
    "chapter_id": "eng_c5_ch06",
    "chapter_no": 6,
    "title": "What a Tank!",
    "book_title": "Santoor",
    "unit_title": "Water",
    "source_url": "https://ncert.nic.in/textbook/pdf/eesa106.pdf",
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
      "anchor_id": "eng_c5_ch06:information:1-4",
      "section_label": "Informational reading and comprehension",
      "page_start": 1,
      "page_end": 4,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa106.pdf#page=1",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch06:language:5-7",
      "section_label": "Contractions, exclamations, and emotion in context",
      "page_start": 5,
      "page_end": 7,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa106.pdf#page=5",
      "coverage_treatment": "taught_and_assessed",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch06:vocabulary:8-9",
      "section_label": "Animal families and sound-versus-meaning vocabulary",
      "page_start": 8,
      "page_end": 9,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa106.pdf#page=8",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch06:conservation:10-11",
      "section_label": "Water-conservation reasoning and communication",
      "page_start": 10,
      "page_end": 11,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa106.pdf#page=10",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch06:inquiry:12-14",
      "section_label": "Inquiry, poster, research, and procedural application",
      "page_start": 12,
      "page_end": 14,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa106.pdf#page=12",
      "coverage_treatment": "textbook_companion",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch06:facilitated:8-14",
      "section_label": "Facilitated listening, speaking, drawing, and role-play extensions",
      "page_start": 8,
      "page_end": 14,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa106.pdf#page=8",
      "coverage_treatment": "offline_group_activity",
      "required_for_chapter_certification": false
    }
  ],
  "levels": [
    {
      "level_id": "tank-purpose-sequence",
      "title": "How Stored Water Moves",
      "focus": "find the main process and place water-system stages in order",
      "outcome": "Explain the purpose of a water-storage system and sequence its important stages from collection to safe use.",
      "skill_ids": [
        "reading.event_sequence",
        "reading.paragraph_main_idea"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch06:information:1-4"
      ],
      "connect": {
        "teaching_block": "A storage system is easier to understand when you follow what happens to water from entry to use. Sequence words and purpose clues keep the explanation accurate.",
        "passage": "A roof channel catches rain, a mesh blocks leaves, a covered tank stores the water, and a tap releases it for the garden.",
        "prompt": "Trace the four stages once, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "tank-purpose-sequence-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Track the water with arrows, then remove decorative details before stating the main process.",
        "passage": "Rain from the library roof enters a mesh screen, flows into a settling drum, and then reaches a covered tank. A hand pump draws the stored water.",
        "prompt": "Which statement gives the main process in the correct order?",
        "skill_ids": [
          "reading.event_sequence",
          "reading.paragraph_main_idea"
        ],
        "options": [
          "screen, settle, store, then pump",
          "pump, store, screen, then settle",
          "store only drinking water from a tap",
          "let roof water enter the pump first"
        ],
        "accepted_answers": [
          "screen, settle, store, then pump"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "tank-purpose-sequence-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "A school garden uses two containers. The upper barrel catches rain. A narrow pipe carries it to a lower drum, and a tap releases it near the vegetable beds.",
          "prompt": "What is the central purpose of this arrangement?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
          ],
          "options": [
            "store rain for later garden use",
            "make the rain fall faster",
            "send vegetables into the drum",
            "replace every water source in school"
          ],
          "accepted_answers": [
            "store rain for later garden use"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "tank-purpose-sequence-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "Before water enters a stone cistern, it passes through gravel and cloth. The cistern has a lid, and families use a small outlet instead of dipping buckets inside.",
          "prompt": "Why are filtering, covering, and using an outlet placed in that order?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
          ],
          "options": [
            "cover the debris before filtering",
            "clean first, protect in storage, then draw safely",
            "draw the water before it is stored",
            "use the steps only to decorate the cistern"
          ],
          "accepted_answers": [
            "clean first, protect in storage, then draw safely"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-purpose-sequence-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "A clay pot inside a shaded box receives water from a rooftop channel. Excess water leaves through an overflow pipe into a flower bed.",
          "prompt": "Which detail shows that the system manages extra water?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
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
                "overflow pipe",
                "excess water",
                "flower bed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "overflow pipe",
            "excess water",
            "flower bed"
          ],
          "model_answer": "The overflow pipe sends excess water from the pot to the flower bed.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-purpose-sequence-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "Workers first mark the tank site, then build a strong base, seal the inner walls, and finally test the tank with a small amount of water.",
          "prompt": "Which step must happen immediately before testing?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
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
                "seal",
                "inner walls",
                "before testing"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "seal",
            "inner walls",
            "before testing"
          ],
          "model_answer": "The inner walls must be sealed immediately before the tank is tested.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-purpose-sequence-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "A hillside tank receives spring water through a pipe. Sand settles at the bottom. Clearer water leaves from an outlet placed above the sediment.",
          "prompt": "Explain how the outlet position helps the system work.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
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
                "above settled sand",
                "clearer water",
                "avoids sediment"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "above settled sand",
            "clearer water",
            "avoids sediment"
          ],
          "model_answer": "Because the outlet is above the settled sand, it releases clearer water instead of pulling sediment from the bottom.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-purpose-sequence-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "During a dry week, the community opens the storage tank only at fixed times. A register records how many buckets each lane receives.",
          "prompt": "State the main idea and one detail that supports it.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
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
                "rationing stored water",
                "fixed times",
                "bucket register"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "rationing stored water",
            "fixed times",
            "bucket register"
          ],
          "model_answer": "The community is rationing stored water fairly; fixed opening times and a bucket register support that idea.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-purpose-sequence-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "A farm pond catches runoff, reeds slow the muddy water, and a small gate later directs water to fruit trees.",
          "prompt": "Summarise the water's route in one ordered sentence.",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
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
                "runoff enters",
                "reeds slow",
                "gate directs"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "runoff enters",
            "reeds slow",
            "gate directs"
          ],
          "model_answer": "Runoff enters the pond, reeds slow and clean it, and the gate later directs it to fruit trees.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-purpose-sequence-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "The apartment tank has a level marker. When the marker reaches red, the caretaker stops the motor so water does not spill from the roof.",
          "prompt": "What problem does the level marker prevent?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
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
                "prevents overfilling",
                "stops motor",
                "water waste"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "prevents overfilling",
            "stops motor",
            "water waste"
          ],
          "model_answer": "It prevents overfilling and wasting water by showing when the motor should be stopped.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "tank-purpose-sequence-misconception",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
          ],
          "misconception": "The learner lists visible parts of a tank but loses the order or confuses one detail with the system's main purpose.",
          "remediation": "Draw an arrow from each stage to the next, then state the shared purpose in one sentence before adding supporting details.",
          "support_check_ids": [
            "tank-purpose-sequence-bridge",
            "tank-purpose-sequence-masterclass",
            "tank-purpose-sequence-revision1",
            "tank-purpose-sequence-revision2",
            "tank-purpose-sequence-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "tank-purpose-sequence-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "Rain from the library roof enters a mesh screen, flows into a settling drum, and then reaches a covered tank. A hand pump draws the stored water.",
          "prompt": "Which statement gives the main process in the correct order?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
          ],
          "options": [
            "pump, store, screen, then settle",
            "store only drinking water from a tap",
            "let roof water enter the pump first",
            "screen, settle, store, then pump"
          ],
          "accepted_answers": [
            "screen, settle, store, then pump"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "tank-purpose-sequence-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "A school garden uses two containers. The upper barrel catches rain. A narrow pipe carries it to a lower drum, and a tap releases it near the vegetable beds.",
          "prompt": "What is the central purpose of this arrangement?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
          ],
          "options": [
            "make the rain fall faster",
            "send vegetables into the drum",
            "replace every water source in school",
            "store rain for later garden use"
          ],
          "accepted_answers": [
            "store rain for later garden use"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "tank-purpose-sequence-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "Before water enters a stone cistern, it passes through gravel and cloth. The cistern has a lid, and families use a small outlet instead of dipping buckets inside.",
          "prompt": "Why are filtering, covering, and using an outlet placed in that order?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
          ],
          "options": [
            "cover the debris before filtering",
            "draw the water before it is stored",
            "clean first, protect in storage, then draw safely",
            "use the steps only to decorate the cistern"
          ],
          "accepted_answers": [
            "clean first, protect in storage, then draw safely"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "tank-purpose-sequence-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "A clay pot inside a shaded box receives water from a rooftop channel. Excess water leaves through an overflow pipe into a flower bed.",
          "prompt": "Which detail shows that the system manages extra water?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
          ],
          "options": [
            "the overflow pipe leads to the flower bed",
            "the clay pot is inside a box",
            "the roof is above the channel",
            "the shade makes rain disappear"
          ],
          "accepted_answers": [
            "the overflow pipe leads to the flower bed"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "tank-purpose-sequence-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Track the water with arrows, then remove decorative details before stating the main process.",
          "passage": "Workers first mark the tank site, then build a strong base, seal the inner walls, and finally test the tank with a small amount of water.",
          "prompt": "Which step must happen immediately before testing?",
          "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea"
          ],
          "options": [
            "mark the site again",
            "empty the finished tank forever",
            "remove the strong base",
            "seal the inner walls"
          ],
          "accepted_answers": [
            "seal the inner walls"
          ]
        }
      }
    },
    {
      "level_id": "tank-design-inference",
      "title": "Design, Identity, and Function",
      "focus": "separate symbolic design clues from practical storage features",
      "outcome": "Use visible details to infer what a design represents and explain separately how a practical feature helps the object work.",
      "skill_ids": [
        "reading.inference_reason",
        "writing.reason_answer"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch06:information:1-4"
      ],
      "connect": {
        "teaching_block": "A painted shape may tell us about an owner or place, while a lid, lining, base, or outlet performs a physical job. Strong inference keeps those roles separate.",
        "passage": "A tailor paints a measuring tape around a drum. The tight lid keeps dust out; the painted tape links the drum to the tailor's work.",
        "prompt": "Name the symbolic clue and the functional clue, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "tank-design-inference-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Label each clue as identity, function, or unsupported guess before writing the reason.",
        "passage": "A baker paints measuring marks like cups on the side of a shop's water drum.",
        "prompt": "What can you reasonably infer about the design choice?",
        "skill_ids": [
          "reading.inference_reason"
        ],
        "options": [
          "the design reflects the baker's work",
          "the drum can bake bread",
          "every baker owns the same drum",
          "the marks prove the water is sweet"
        ],
        "accepted_answers": [
          "the design reflects the baker's work"
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-design-inference-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A bicycle repairer adds a wheel pattern around a rain barrel but keeps the lid and tap easy to use.",
          "prompt": "Which claim is supported by both function and identity?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "stores water safely",
                "wheel pattern",
                "occupation"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "stores water safely",
            "wheel pattern",
            "occupation"
          ],
          "model_answer": "The barrel still stores water safely while the wheel pattern represents the repairer's occupation.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-design-inference-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "At a music school, a tank is painted with rhythm lines. Its wide base, not the paint, keeps it stable.",
          "prompt": "Which detail is functional rather than symbolic?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "wide base",
                "keeps stable"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "wide base",
            "keeps stable"
          ],
          "model_answer": "The wide base is functional because it keeps the tank stable.",
          "pass_score": 0.8
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-design-inference-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A fisher chooses a fish-shaped sign above a plain underground tank. The sign marks the family trade; the underground chamber keeps water cool.",
          "prompt": "Explain the two different jobs performed by the sign and chamber.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "sign represents trade",
                "chamber keeps cool"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "sign represents trade",
            "chamber keeps cool"
          ],
          "model_answer": "The fish sign represents the family's trade, while the underground chamber helps keep stored water cool.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-design-inference-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A tailor's storage drum has a painted tape-measure band and a tight cover.",
          "prompt": "Which interpretation uses evidence instead of guessing?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "tape-measure band",
                "tailoring",
                "cover protects"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "tape-measure band",
            "tailoring",
            "cover protects"
          ],
          "model_answer": "The tape-measure band links the drum to tailoring, and the tight cover protects the water.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-design-inference-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A pottery club builds a rounded cistern and presses clay-leaf patterns into the outer plaster. A separate inner lining prevents leaks.",
          "prompt": "Why is the inner lining more important to storage than the leaf pattern?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "lining prevents leaks",
                "pattern shows identity"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "lining prevents leaks",
            "pattern shows identity"
          ],
          "model_answer": "The inner lining prevents water from leaking, whereas the leaf pattern communicates the club's craft identity.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-design-inference-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A school science team paints a rainfall scale on a tank. Students record the level each Monday.",
          "prompt": "What conclusion is supported about the scale?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "observing level",
                "recording changes",
                "scale"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "observing level",
            "recording changes",
            "scale"
          ],
          "model_answer": "The scale turns the tank into a tool for observing and recording changes in stored water.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-design-inference-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "Two tanks have peacock paintings. Only one has a secure lid, cleaned inlet, and working overflow pipe.",
          "prompt": "Which tank is better designed for safe storage, and why?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "secure lid",
                "clean inlet",
                "overflow"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "secure lid",
            "clean inlet",
            "overflow"
          ],
          "model_answer": "The tank with the lid, clean inlet, and overflow is safer because those features manage contamination and excess water.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-design-inference-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A carpenter builds a wooden sign shaped like a saw beside a masonry tank. The sign identifies the workshop, but it never touches the water.",
          "prompt": "What evidence stops us from claiming that the saw sign filters water?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "never touches water",
                "identifies workshop"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "never touches water",
            "identifies workshop"
          ],
          "model_answer": "The sign never touches the water and is described only as identifying the workshop.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "tank-design-inference-misconception",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "misconception": "The learner treats decoration as proof of physical safety or invents an owner's intention without a visible clue.",
          "remediation": "Use a two-column evidence chart: what the detail represents and what the detail physically does; reject any claim with no matching clue.",
          "support_check_ids": [
            "tank-design-inference-bridge",
            "tank-design-inference-masterclass",
            "tank-design-inference-revision1",
            "tank-design-inference-revision2",
            "tank-design-inference-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "tank-design-inference-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A baker paints measuring marks like cups on the side of a shop's water drum.",
          "prompt": "What can you reasonably infer about the design choice?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "cup-shaped marks",
                "baker",
                "measuring ingredients"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "cup-shaped marks",
            "baker",
            "measuring ingredients"
          ],
          "model_answer": "The cup-shaped marks connect the drum with the baker's daily work of measuring ingredients.",
          "pass_score": 0.8
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "tank-design-inference-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A bicycle repairer adds a wheel pattern around a rain barrel but keeps the lid and tap easy to use.",
          "prompt": "Which claim is supported by both function and identity?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "stores water safely",
                "wheel pattern",
                "occupation"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "stores water safely",
            "wheel pattern",
            "occupation"
          ],
          "model_answer": "The barrel still stores water safely while the wheel pattern represents the repairer's occupation.",
          "pass_score": 0.8
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "tank-design-inference-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "At a music school, a tank is painted with rhythm lines. Its wide base, not the paint, keeps it stable.",
          "prompt": "Which detail is functional rather than symbolic?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "wide base",
                "keeps stable"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "wide base",
            "keeps stable"
          ],
          "model_answer": "The wide base is functional because it keeps the tank stable.",
          "pass_score": 0.8
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "tank-design-inference-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A fisher chooses a fish-shaped sign above a plain underground tank. The sign marks the family trade; the underground chamber keeps water cool.",
          "prompt": "Explain the two different jobs performed by the sign and chamber.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "sign represents trade",
                "chamber keeps cool"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "sign represents trade",
            "chamber keeps cool"
          ],
          "model_answer": "The fish sign represents the family's trade, while the underground chamber helps keep stored water cool.",
          "pass_score": 0.8
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "tank-design-inference-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Label each clue as identity, function, or unsupported guess before writing the reason.",
          "passage": "A tailor's storage drum has a painted tape-measure band and a tight cover.",
          "prompt": "Which interpretation uses evidence instead of guessing?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
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
                "tape-measure band",
                "tailoring",
                "cover protects"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "tape-measure band",
            "tailoring",
            "cover protects"
          ],
          "model_answer": "The tape-measure band links the drum to tailoring, and the tight cover protects the water.",
          "pass_score": 0.8
        }
      }
    },
    {
      "level_id": "tank-contractions",
      "title": "Join Words Without Losing Meaning",
      "focus": "form standard contractions inside complete sentences",
      "outcome": "Rewrite verb groups as standard contractions with correct apostrophes while preserving subject, tense, and sentence meaning.",
      "skill_ids": [
        "grammar.sentence_order",
        "writing.complete_sentence"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch06:language:5-7"
      ],
      "connect": {
        "teaching_block": "A contraction shortens a familiar verb group without changing its time or meaning. The apostrophe marks letters that were removed; it is not decoration.",
        "passage": "They are checking the lid, but they have not opened the tank becomes: They're checking the lid, but they haven't opened the tank.",
        "prompt": "Expand both contractions once, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "tank-contractions-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
        "passage": "The tank is not full yet, so Meera will not switch off the inlet.",
        "prompt": "Rewrite both bold ideas naturally with contractions.",
        "skill_ids": [
          "grammar.sentence_order"
        ],
        "options": [
          "The tank is'nt full, so Meera will'nt switch it off.",
          "The tank not full, Meera wont switches.",
          "The tank isn't full yet, so Meera won't switch off the inlet.",
          "The tank isn't full, so Meera wouldn't switched."
        ],
        "accepted_answers": [
          "The tank isn't full yet, so Meera won't switch off the inlet."
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-contractions-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "We do not waste the first bucket, and we cannot leave the tap open.",
          "prompt": "Write the sentence using standard contractions.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "don't",
                "can't"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "don't",
            "can't"
          ],
          "model_answer": "We don't waste the first bucket, and we can't leave the tap open.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-contractions-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "Ravi has not checked the lid because it is not his turn.",
          "prompt": "Choose the correctly contracted version.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "hasn't",
                "isn't"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "hasn't",
            "isn't"
          ],
          "model_answer": "Ravi hasn't checked the lid because it isn't his turn.",
          "pass_score": 0.8
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-contractions-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "They are cleaning the channel, but they have not opened the tank.",
          "prompt": "Which rewrite keeps the meaning and uses contractions correctly?",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "they're",
                "haven't"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "they're",
            "haven't"
          ],
          "model_answer": "They're cleaning the channel, but they haven't opened the tank.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-contractions-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "I would check the overflow if I were there, but I am not at school today.",
          "prompt": "Contract the two suitable verb groups.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "I'd",
                "I'm"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "I'd",
            "I'm"
          ],
          "model_answer": "I'd check the overflow if I were there, but I'm not at school today.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-contractions-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "The pipe does not reach the garden, so the workers will not bury it yet.",
          "prompt": "Write a complete sentence using doesn't and won't correctly.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "doesn't reach",
                "won't bury"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "doesn't reach",
            "won't bury"
          ],
          "model_answer": "The pipe doesn't reach the garden, so the workers won't bury it yet.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-contractions-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "Sana is not guessing; she has not finished measuring the water level.",
          "prompt": "Rewrite the sentence with standard contractions and unchanged meaning.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "isn't guessing",
                "hasn't finished"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "isn't guessing",
            "hasn't finished"
          ],
          "model_answer": "Sana isn't guessing; she hasn't finished measuring the water level.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-contractions-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "You should not touch the inlet because it is not clean.",
          "prompt": "Produce the sentence with two accurate contractions.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "shouldn't touch",
                "isn't clean"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "shouldn't touch",
            "isn't clean"
          ],
          "model_answer": "You shouldn't touch the inlet because it isn't clean.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-contractions-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "The volunteers were not late, and they did not forget the cleaning brushes.",
          "prompt": "Use contractions while preserving past time.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "weren't late",
                "didn't forget"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "weren't late",
            "didn't forget"
          ],
          "model_answer": "The volunteers weren't late, and they didn't forget the cleaning brushes.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "tank-contractions-misconception",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
          ],
          "misconception": "The learner drops a subject or verb, changes tense, or places an apostrophe by sound instead of marking omitted letters.",
          "remediation": "Use four checks in order: expand, preserve tense, remove exact letters, and place the apostrophe where those letters were removed.",
          "support_check_ids": [
            "tank-contractions-bridge",
            "tank-contractions-masterclass",
            "tank-contractions-revision1",
            "tank-contractions-revision2",
            "tank-contractions-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "tank-contractions-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "The tank is not full yet, so Meera will not switch off the inlet.",
          "prompt": "Rewrite both bold ideas naturally with contractions.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "isn't",
                "won't"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "isn't",
            "won't"
          ],
          "model_answer": "The tank isn't full yet, so Meera won't switch off the inlet.",
          "pass_score": 0.8
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "tank-contractions-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "We do not waste the first bucket, and we cannot leave the tap open.",
          "prompt": "Write the sentence using standard contractions.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "don't",
                "can't"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "don't",
            "can't"
          ],
          "model_answer": "We don't waste the first bucket, and we can't leave the tap open.",
          "pass_score": 0.8
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "tank-contractions-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "Ravi has not checked the lid because it is not his turn.",
          "prompt": "Choose the correctly contracted version.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "hasn't",
                "isn't"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "hasn't",
            "isn't"
          ],
          "model_answer": "Ravi hasn't checked the lid because it isn't his turn.",
          "pass_score": 0.8
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "tank-contractions-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "They are cleaning the channel, but they have not opened the tank.",
          "prompt": "Which rewrite keeps the meaning and uses contractions correctly?",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "they're",
                "haven't"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "they're",
            "haven't"
          ],
          "model_answer": "They're cleaning the channel, but they haven't opened the tank.",
          "pass_score": 0.8
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "tank-contractions-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Expand the contraction first, identify omitted letters, and then rebuild the complete sentence with the apostrophe in their place.",
          "passage": "I would check the overflow if I were there, but I am not at school today.",
          "prompt": "Contract the two suitable verb groups.",
          "skill_ids": [
            "grammar.sentence_order",
            "writing.complete_sentence"
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
                "I'd",
                "I'm"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "I'd",
            "I'm"
          ],
          "model_answer": "I'd check the overflow if I were there, but I'm not at school today.",
          "pass_score": 0.8
        }
      }
    },
    {
      "level_id": "tank-exclamation-emotion",
      "title": "Read the Feeling Behind the Mark",
      "focus": "use event context and punctuation to infer a precise emotion",
      "outcome": "Interpret an exclamation by naming the likely emotion or urgency and supporting it with a contextual clue rather than punctuation alone.",
      "skill_ids": [
        "grammar.punctuation_capitalization",
        "reading.sentence_comprehension"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch06:language:5-7"
      ],
      "connect": {
        "teaching_block": "An exclamation mark shows strong force, but it does not name one fixed feeling. The surrounding event distinguishes joy, alarm, relief, admiration, and surprise.",
        "passage": "At last! The repaired tap has stopped dripping. The words 'at last' and the successful repair suggest relief.",
        "prompt": "Identify the feeling and its clue, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "tank-exclamation-emotion-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
        "passage": "The last drop splashed into the empty bucket just as the supply stopped!",
        "prompt": "Which emotion best fits the exclamation in this situation?",
        "skill_ids": [
          "grammar.punctuation_capitalization",
          "reading.sentence_comprehension"
        ],
        "options": [
          "boredom because nothing happened",
          "anger at a full river",
          "relief mixed with surprise",
          "sleepiness caused by punctuation"
        ],
        "accepted_answers": [
          "relief mixed with surprise"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "tank-exclamation-emotion-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "Look! The overflow is rushing toward the classroom door!",
          "prompt": "What does the exclamation mark help the speaker communicate?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension"
          ],
          "options": [
            "a calm historical fact",
            "a polite closing",
            "uncertainty about whether a door exists",
            "urgent alarm"
          ],
          "accepted_answers": [
            "urgent alarm"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "tank-exclamation-emotion-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "What a clever way to reuse rinse water for the plants!",
          "prompt": "Identify the feeling and the clue that creates it.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension"
          ],
          "options": [
            "fear of all plants",
            "dislike of every reuse idea",
            "admiration for a clever idea",
            "confusion about what water is"
          ],
          "accepted_answers": [
            "admiration for a clever idea"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-exclamation-emotion-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "Oh no! The tap has been dripping all night!",
          "prompt": "Which response explains both punctuation and context?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
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
                "worry",
                "all night",
                "wasted water"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "worry",
            "all night",
            "wasted water"
          ],
          "model_answer": "The punctuation intensifies worry because the overnight drip has wasted water.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-exclamation-emotion-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "Hurray! Our repaired channel carried rain into the tank!",
          "prompt": "What emotion is expressed, and why?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
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
                "joy",
                "repaired channel",
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
            "joy",
            "repaired channel",
            "success"
          ],
          "model_answer": "The speaker expresses joy because the repaired channel successfully collected rainwater.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-exclamation-emotion-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "The caretaker whispered, 'Careful!' when a child stepped near the wet floor.",
          "prompt": "Explain how the exclamation works even though the voice is quiet.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
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
                "strong warning",
                "wet floor",
                "not loudness"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "strong warning",
            "wet floor",
            "not loudness"
          ],
          "model_answer": "The exclamation marks a strong warning; loudness is not required when the situation is urgent.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-exclamation-emotion-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "Wonderful! Every class reduced its water use this week.",
          "prompt": "Use evidence to name the speaker's emotion.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
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
                "pleased",
                "proud",
                "reduced use"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "pleased",
            "proud",
            "reduced use"
          ],
          "model_answer": "The speaker feels pleased or proud because every class achieved a reduction in water use.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-exclamation-emotion-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "Stop! The cleaning liquid must not enter the drinking-water tank!",
          "prompt": "Why is an exclamation more suitable than a full stop here?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
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
                "immediate danger",
                "urgent action",
                "contamination"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "immediate danger",
            "urgent action",
            "contamination"
          ],
          "model_answer": "The exclamation signals an immediate danger and demands urgent action to prevent contamination.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-exclamation-emotion-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "'At last!' Rohan said when the blocked pipe began to flow.",
          "prompt": "What does 'At last!' reveal about the earlier situation?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
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
                "relief",
                "delay",
                "blocked pipe"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "relief",
            "delay",
            "blocked pipe"
          ],
          "model_answer": "It reveals relief after a delay or difficulty, because the pipe had been blocked.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "tank-exclamation-emotion-misconception",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension"
          ],
          "misconception": "The learner assumes every exclamation expresses happiness or identifies a feeling without using the event as evidence.",
          "remediation": "Cover the punctuation, infer the feeling from words and events, then uncover the mark and explain how it strengthens that meaning.",
          "support_check_ids": [
            "tank-exclamation-emotion-bridge",
            "tank-exclamation-emotion-masterclass",
            "tank-exclamation-emotion-revision1",
            "tank-exclamation-emotion-revision2",
            "tank-exclamation-emotion-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "tank-exclamation-emotion-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "The last drop splashed into the empty bucket just as the supply stopped!",
          "prompt": "Which emotion best fits the exclamation in this situation?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension"
          ],
          "options": [
            "boredom because nothing happened",
            "anger at a full river",
            "relief mixed with surprise",
            "sleepiness caused by punctuation"
          ],
          "accepted_answers": [
            "relief mixed with surprise"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "tank-exclamation-emotion-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "Look! The overflow is rushing toward the classroom door!",
          "prompt": "What does the exclamation mark help the speaker communicate?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension"
          ],
          "options": [
            "a calm historical fact",
            "urgent alarm",
            "a polite closing",
            "uncertainty about whether a door exists"
          ],
          "accepted_answers": [
            "urgent alarm"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "tank-exclamation-emotion-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "What a clever way to reuse rinse water for the plants!",
          "prompt": "Identify the feeling and the clue that creates it.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension"
          ],
          "options": [
            "admiration for a clever idea",
            "fear of all plants",
            "dislike of every reuse idea",
            "confusion about what water is"
          ],
          "accepted_answers": [
            "admiration for a clever idea"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "tank-exclamation-emotion-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "Oh no! The tap has been dripping all night!",
          "prompt": "Which response explains both punctuation and context?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension"
          ],
          "options": [
            "joy because the tap works perfectly",
            "calmness about saving water",
            "worry about overnight waste",
            "a question asking who owns night"
          ],
          "accepted_answers": [
            "worry about overnight waste"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "tank-exclamation-emotion-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Read the event before the exclamation, name what changed, and choose the emotion that fits that change.",
          "passage": "Hurray! Our repaired channel carried rain into the tank!",
          "prompt": "What emotion is expressed, and why?",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension"
          ],
          "options": [
            "joy at successful collection",
            "sadness that the repair worked",
            "anger at an empty channel",
            "doubt about whether rain exists"
          ],
          "accepted_answers": [
            "joy at successful collection"
          ]
        }
      }
    },
    {
      "level_id": "tank-animal-word-meaning",
      "title": "Animal Families and Meaning Clues",
      "focus": "use relationships and actions to select precise vocabulary meanings",
      "outcome": "Identify animal-family terms and distinguish similar-sounding or multiple-meaning words through the surrounding relationship, place, and action.",
      "skill_ids": [
        "vocab.chapter_word_usage",
        "reading.word_meaning_context"
      ],
      "episode_kind": "meaning_encounter",
      "source_anchor_ids": [
        "eng_c5_ch06:vocabulary:8-9"
      ],
      "connect": {
        "teaching_block": "Precise animal words show adult, young, or group relationships. Other words may sound alike or carry more than one meaning, so context must decide.",
        "passage": "The mare stood beside her foal. 'Mare' names the adult female horse, and 'foal' names the young horse because the relationship is explicit.",
        "prompt": "Mark the adult-young relationship, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "tank-animal-word-meaning-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
        "passage": "A young goat stayed close to the adult female goat while the herd crossed the path.",
        "prompt": "Which animal-family word correctly names the young goat?",
        "skill_ids": [
          "vocab.chapter_word_usage",
          "reading.word_meaning_context"
        ],
        "options": [
          "kid",
          "calf",
          "foal",
          "cub"
        ],
        "accepted_answers": [
          "kid"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "tank-animal-word-meaning-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "The stable worker guided the adult male horse away from the mare and her foal.",
          "prompt": "Which word in the sentence names the young horse?",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
          ],
          "options": [
            "foal",
            "mare",
            "herd",
            "stable"
          ],
          "accepted_answers": [
            "foal"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "tank-animal-word-meaning-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "A hen gathered her chicks under a low shelter when rain began.",
          "prompt": "What does 'chicks' mean in this context?",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
          ],
          "options": [
            "adult ducks",
            "young chickens",
            "bird shelters",
            "rain clouds"
          ],
          "accepted_answers": [
            "young chickens"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-animal-word-meaning-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "The wildlife keeper saw a lioness lead two cubs toward shade.",
          "prompt": "Which relationship is expressed by 'lioness' and 'cubs'?",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
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
                "adult female lion",
                "young lions"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "adult female lion",
            "young lions"
          ],
          "model_answer": "A lioness is an adult female lion, and cubs are young lions.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-animal-word-meaning-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "A duck and her ducklings paddled near the reeds.",
          "prompt": "Choose the sentence that uses 'ducklings' accurately.",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
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
                "young ducks",
                "following adult"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "young ducks",
            "following adult"
          ],
          "model_answer": "The ducklings were the young ducks following the adult.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-animal-word-meaning-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "The word 'calf' can name a young cow, while 'calf muscle' names part of a person's lower leg.",
          "prompt": "Explain how context selects the meaning in 'The calf followed the cow'.",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
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
                "cow",
                "followed",
                "young cow"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "cow",
            "followed",
            "young cow"
          ],
          "model_answer": "Because the sentence includes a cow and an animal action, 'calf' means a young cow.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-animal-word-meaning-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "Nisha heard 'pail' and 'pale'. One means a bucket; the other describes a light colour.",
          "prompt": "Write a sentence that proves you mean the bucket word.",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
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
                "pail",
                "bucket",
                "carried water"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "pail",
            "bucket",
            "carried water"
          ],
          "model_answer": "Nisha carried a pail of water from the tap.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-animal-word-meaning-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "The words 'tank' and 'thank' sound close, but one stores material and the other expresses gratitude.",
          "prompt": "Use both words so their meanings are clear.",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
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
                "thanked",
                "gratitude",
                "water tank"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "thanked",
            "gratitude",
            "water tank"
          ],
          "model_answer": "I thanked the caretaker for cleaning the water tank.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-animal-word-meaning-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "A brood of chicks moved behind the hen, while a flock of adult birds flew overhead.",
          "prompt": "How do 'brood' and 'flock' differ here?",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
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
                "brood young chicks",
                "flock birds"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "brood young chicks",
            "flock birds"
          ],
          "model_answer": "The brood is the group of young chicks, while the flock is the larger group of birds flying together.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "tank-animal-word-meaning-misconception",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
          ],
          "misconception": "The learner chooses a familiar sound or animal label without checking the relationship and action in the sentence.",
          "remediation": "Build a small relation map for animal terms, and for ambiguous words substitute each meaning back into the sentence to see which one fits.",
          "support_check_ids": [
            "tank-animal-word-meaning-bridge",
            "tank-animal-word-meaning-masterclass",
            "tank-animal-word-meaning-revision1",
            "tank-animal-word-meaning-revision2",
            "tank-animal-word-meaning-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "tank-animal-word-meaning-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "A young goat stayed close to the adult female goat while the herd crossed the path.",
          "prompt": "Which animal-family word correctly names the young goat?",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
          ],
          "options": [
            "kid",
            "calf",
            "foal",
            "cub"
          ],
          "accepted_answers": [
            "kid"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "tank-animal-word-meaning-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "The stable worker guided the adult male horse away from the mare and her foal.",
          "prompt": "Which word in the sentence names the young horse?",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
          ],
          "options": [
            "mare",
            "foal",
            "herd",
            "stable"
          ],
          "accepted_answers": [
            "foal"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "tank-animal-word-meaning-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "A hen gathered her chicks under a low shelter when rain began.",
          "prompt": "What does 'chicks' mean in this context?",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
          ],
          "options": [
            "adult ducks",
            "young chickens",
            "bird shelters",
            "rain clouds"
          ],
          "accepted_answers": [
            "young chickens"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "tank-animal-word-meaning-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "The wildlife keeper saw a lioness lead two cubs toward shade.",
          "prompt": "Which relationship is expressed by 'lioness' and 'cubs'?",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
          ],
          "options": [
            "male bird and eggs",
            "adult female and young lions",
            "young horse and stable",
            "fish and pond"
          ],
          "accepted_answers": [
            "adult female and young lions"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "tank-animal-word-meaning-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Circle the relationship or action clue, then test each possible meaning inside the whole sentence.",
          "passage": "A duck and her ducklings paddled near the reeds.",
          "prompt": "Choose the sentence that uses 'ducklings' accurately.",
          "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context"
          ],
          "options": [
            "The ducklings were adult goats.",
            "Ducklings are the reeds beside a pond.",
            "The duckling was a group of boats.",
            "The ducklings were young ducks."
          ],
          "accepted_answers": [
            "The ducklings were young ducks."
          ]
        }
      }
    },
    {
      "level_id": "tank-conservation-paragraph",
      "title": "Turn a Slogan into an Action Plan",
      "focus": "develop a focused conservation paragraph with connectors",
      "outcome": "Write an organised paragraph that identifies a real waste, proposes a practical action, explains its benefit, and states a needed safety or feasibility boundary.",
      "skill_ids": [
        "grammar.connectors_because_and_but",
        "writing.paragraph"
      ],
      "episode_kind": "expression_workshop",
      "source_anchor_ids": [
        "eng_c5_ch06:conservation:10-11"
      ],
      "connect": {
        "teaching_block": "A conservation message becomes useful when it moves beyond a slogan. It should name the observed problem, give a doable action, explain why it helps, and keep safety limits visible.",
        "passage": "The tap drips all night. Report the leak and close the supply valve if an adult authorises it, because stopping the flow prevents waste; however, the damaged part still needs repair.",
        "prompt": "Locate the problem, action, reason, and boundary, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "tank-conservation-paragraph-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
        "passage": "The art room tap drips between classes. A tray can catch the clean drips for washing brushes until the washer is repaired.",
        "prompt": "Write a short conservation paragraph that names the problem, gives an immediate action, explains why it helps, and notes the permanent fix.",
        "skill_ids": [
          "grammar.connectors_because_and_but"
        ],
        "options": [
          "ignore the drip because it is small",
          "catch and reuse drips, then repair the washer",
          "leave the tap open for convenience",
          "write only 'save water' without an action"
        ],
        "accepted_answers": [
          "catch and reuse drips, then repair the washer"
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "A gardener uses a hose at noon, and much of the spray lands on the path. A watering can can target plant roots early in the morning.",
          "prompt": "Develop a paragraph recommending the better practice with a reason and contrast.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "recommendation",
              "description": "States the better practice.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains how it saves water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "contrast",
              "description": "Contrasts the weaker practice.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "recommendation",
              "description": "States the better practice.",
              "any_of": [
                "watering can",
                "early morning",
                "target roots"
              ]
            },
            {
              "id": "reason",
              "description": "Explains how it saves water.",
              "any_of": [
                "less evaporation",
                "less spray on path"
              ]
            },
            {
              "id": "contrast",
              "description": "Contrasts the weaker practice.",
              "any_of": [
                "hose",
                "scattered spray",
                "wastes water"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "watering can",
            "early morning",
            "target roots",
            "less evaporation",
            "less spray on path",
            "hose",
            "scattered spray",
            "wastes water"
          ],
          "model_answer": "The gardener should water the roots with a can early in the morning because less water will evaporate or land on the path. The hose is faster, but its scattered spray wastes water in this situation.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "During handwashing, several children keep the tap running while using soap. A class sign suggests wet, turn off, soap, rinse.",
          "prompt": "Write a clear action paragraph using sequence words and a reason.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "sequence",
              "description": "Gives the action in order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Connects the sequence to saving water.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sequence",
              "description": "Gives the action in order.",
              "any_of": [
                "first wet",
                "turn off while soaping",
                "finally rinse"
              ]
            },
            {
              "id": "reason",
              "description": "Connects the sequence to saving water.",
              "any_of": [
                "tap does not run",
                "saves water"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "first wet",
            "turn off while soaping",
            "finally rinse",
            "tap does not run",
            "saves water"
          ],
          "model_answer": "First wet your hands, then turn off the tap while soaping, and finally turn it on briefly to rinse. This sequence saves water because the tap does not run when no water is needed.",
          "pass_score": 0.8
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "The lunch area has leftover drinking water in many bottles. A labelled container could collect it for cleaning the outdoor floor.",
          "prompt": "Write a paragraph that proposes the reuse safely and sets one boundary.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "proposal",
              "description": "States a safe reuse.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "benefit",
              "description": "Explains the conservation benefit.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "States what must not be collected.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "proposal",
              "description": "States a safe reuse.",
              "any_of": [
                "labelled container",
                "clean outdoor floor"
              ]
            },
            {
              "id": "benefit",
              "description": "Explains the conservation benefit.",
              "any_of": [
                "reuses leftover water",
                "not discarded"
              ]
            },
            {
              "id": "boundary",
              "description": "States what must not be collected.",
              "any_of": [
                "food",
                "soap",
                "not go"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "labelled container",
            "clean outdoor floor",
            "reuses leftover water",
            "not discarded",
            "food",
            "soap",
            "not go"
          ],
          "model_answer": "Students can pour untouched leftover drinking water into a labelled container for cleaning the outdoor floor. This reuses water that would be discarded, but water mixed with food or soap should not go into the container.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "A family washes vegetables in a bowl and then pours the plain water onto balcony plants.",
          "prompt": "Explain why this is useful and when it would not be suitable.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "benefit",
              "description": "Explains the useful reuse.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "Names unsuitable contamination.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "benefit",
              "description": "Explains the useful reuse.",
              "any_of": [
                "rinse water",
                "plants",
                "saves fresh water"
              ]
            },
            {
              "id": "boundary",
              "description": "Names unsuitable contamination.",
              "any_of": [
                "salt",
                "detergent",
                "oil"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "rinse water",
            "plants",
            "saves fresh water",
            "salt",
            "detergent",
            "oil"
          ],
          "model_answer": "Reusing plain vegetable-rinse water on plants saves fresh water. However, water containing salt, detergent, or oil should not be used on the plants.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "The school notices that a toilet cistern continues filling after every flush. The caretaker can close the supply valve until the part is repaired.",
          "prompt": "Write a focused paragraph with the observed evidence, immediate response, and next step.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "evidence",
              "description": "Names the observed problem.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "response",
              "description": "Gives the immediate safe response.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "Gives the permanent next step.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "evidence",
              "description": "Names the observed problem.",
              "any_of": [
                "continues filling",
                "after flush"
              ]
            },
            {
              "id": "response",
              "description": "Gives the immediate safe response.",
              "any_of": [
                "close supply valve",
                "stop waste"
              ]
            },
            {
              "id": "next",
              "description": "Gives the permanent next step.",
              "any_of": [
                "repair faulty part",
                "before normal use"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "continues filling",
            "after flush",
            "close supply valve",
            "stop waste",
            "repair faulty part",
            "before normal use"
          ],
          "model_answer": "The cistern is malfunctioning because water continues to enter after the flush. The caretaker should close the supply valve to stop further waste, and the faulty part should then be repaired before normal use resumes.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "A rooftop tank overflows every evening because the motor is switched off late. A float switch or timed checking routine could stop the overflow.",
          "prompt": "Recommend one solution and justify it in an organised paragraph.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "solution",
              "description": "Recommends a workable solution.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains why it works.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "interim",
              "description": "Acknowledges an interim action or limitation.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "solution",
              "description": "Recommends a workable solution.",
              "any_of": [
                "float switch",
                "stop motor"
              ]
            },
            {
              "id": "reason",
              "description": "Explains why it works.",
              "any_of": [
                "safe level",
                "prevents overflow"
              ]
            },
            {
              "id": "interim",
              "description": "Acknowledges an interim action or limitation.",
              "any_of": [
                "timed checking",
                "depends on remembering"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "float switch",
            "stop motor",
            "safe level",
            "prevents overflow",
            "timed checking",
            "depends on remembering"
          ],
          "model_answer": "The building should install a working float switch because it can stop the motor when the tank reaches its safe level. Until then, a timed checking routine is needed, but it depends on someone remembering every evening.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "The sports field is watered even after heavy rain. A simple rain log could help the grounds team decide whether watering is needed.",
          "prompt": "Write a paragraph connecting observation, decision, and benefit.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "observation",
              "description": "Names the evidence to record.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "States the resulting action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "benefit",
              "description": "Explains the saved resource.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "observation",
              "description": "Names the evidence to record.",
              "any_of": [
                "recent rain",
                "soil already wet"
              ]
            },
            {
              "id": "decision",
              "description": "States the resulting action.",
              "any_of": [
                "delay irrigation",
                "check before watering"
              ]
            },
            {
              "id": "benefit",
              "description": "Explains the saved resource.",
              "any_of": [
                "avoids stored water",
                "nature supplied enough"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "recent rain",
            "soil already wet",
            "delay irrigation",
            "check before watering",
            "avoids stored water",
            "nature supplied enough"
          ],
          "model_answer": "The grounds team should record recent rain before watering the field. If the soil is already wet, they can delay irrigation, which avoids using stored water when nature has supplied enough.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "A poster says only 'SAVE WATER' in large letters. It gives no action, reason, audience, or event details.",
          "prompt": "Improve the poster message as a short paragraph for students.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "action",
              "description": "Gives specific learner actions.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains why action matters.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "detail",
              "description": "Adds a relevant event or audience detail.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "action",
              "description": "Gives specific learner actions.",
              "any_of": [
                "turn off taps",
                "report leaks"
              ]
            },
            {
              "id": "reason",
              "description": "Explains why action matters.",
              "any_of": [
                "drip",
                "wasting water"
              ]
            },
            {
              "id": "detail",
              "description": "Adds a relevant event or audience detail.",
              "any_of": [
                "Friday leak check",
                "assembly area"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "turn off taps",
            "report leaks",
            "drip",
            "wasting water",
            "Friday leak check",
            "assembly area"
          ],
          "model_answer": "Turn off classroom taps fully after use and report leaks to the office, because one unnoticed drip continues wasting water all day. Join the Friday leak check near the assembly area.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "tank-conservation-paragraph-misconception",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "misconception": "The learner writes a general slogan or unsupported command without identifying the observed waste, mechanism, or practical boundary.",
          "remediation": "Use a four-box organiser and require one sentence for each box before combining them with because, and, or but.",
          "support_check_ids": [
            "tank-conservation-paragraph-bridge",
            "tank-conservation-paragraph-masterclass",
            "tank-conservation-paragraph-revision1",
            "tank-conservation-paragraph-revision2",
            "tank-conservation-paragraph-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "The art room tap drips between classes. A tray can catch the clean drips for washing brushes until the washer is repaired.",
          "prompt": "Write a short conservation paragraph that names the problem, gives an immediate action, explains why it helps, and notes the permanent fix.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "problem",
              "description": "Names the specific waste.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "action",
              "description": "Gives a workable immediate action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains the benefit.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Names the permanent fix or limitation.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "problem",
              "description": "Names the specific waste.",
              "any_of": [
                "tap drips",
                "leaking tap"
              ]
            },
            {
              "id": "action",
              "description": "Gives a workable immediate action.",
              "any_of": [
                "catch the drips",
                "use them to rinse brushes"
              ]
            },
            {
              "id": "reason",
              "description": "Explains the benefit.",
              "any_of": [
                "prevents waste",
                "useful water"
              ]
            },
            {
              "id": "limit",
              "description": "Names the permanent fix or limitation.",
              "any_of": [
                "repair the washer",
                "fix the leak"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "tap drips",
            "leaking tap",
            "catch the drips",
            "use them to rinse brushes",
            "prevents waste",
            "useful water",
            "repair the washer",
            "fix the leak"
          ],
          "model_answer": "The art-room tap is wasting clean water. We can catch the drips in a tray and use them to rinse brushes, because this prevents useful water from going straight down the drain. However, the washer must still be repaired to stop the leak.",
          "pass_score": 0.8
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "A gardener uses a hose at noon, and much of the spray lands on the path. A watering can can target plant roots early in the morning.",
          "prompt": "Develop a paragraph recommending the better practice with a reason and contrast.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "recommendation",
              "description": "States the better practice.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains how it saves water.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "contrast",
              "description": "Contrasts the weaker practice.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "recommendation",
              "description": "States the better practice.",
              "any_of": [
                "watering can",
                "early morning",
                "target roots"
              ]
            },
            {
              "id": "reason",
              "description": "Explains how it saves water.",
              "any_of": [
                "less evaporation",
                "less spray on path"
              ]
            },
            {
              "id": "contrast",
              "description": "Contrasts the weaker practice.",
              "any_of": [
                "hose",
                "scattered spray",
                "wastes water"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "watering can",
            "early morning",
            "target roots",
            "less evaporation",
            "less spray on path",
            "hose",
            "scattered spray",
            "wastes water"
          ],
          "model_answer": "The gardener should water the roots with a can early in the morning because less water will evaporate or land on the path. The hose is faster, but its scattered spray wastes water in this situation.",
          "pass_score": 0.8
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "During handwashing, several children keep the tap running while using soap. A class sign suggests wet, turn off, soap, rinse.",
          "prompt": "Write a clear action paragraph using sequence words and a reason.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "sequence",
              "description": "Gives the action in order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Connects the sequence to saving water.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sequence",
              "description": "Gives the action in order.",
              "any_of": [
                "first wet",
                "turn off while soaping",
                "finally rinse"
              ]
            },
            {
              "id": "reason",
              "description": "Connects the sequence to saving water.",
              "any_of": [
                "tap does not run",
                "saves water"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "first wet",
            "turn off while soaping",
            "finally rinse",
            "tap does not run",
            "saves water"
          ],
          "model_answer": "First wet your hands, then turn off the tap while soaping, and finally turn it on briefly to rinse. This sequence saves water because the tap does not run when no water is needed.",
          "pass_score": 0.8
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "The lunch area has leftover drinking water in many bottles. A labelled container could collect it for cleaning the outdoor floor.",
          "prompt": "Write a paragraph that proposes the reuse safely and sets one boundary.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "proposal",
              "description": "States a safe reuse.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "benefit",
              "description": "Explains the conservation benefit.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "States what must not be collected.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "proposal",
              "description": "States a safe reuse.",
              "any_of": [
                "labelled container",
                "clean outdoor floor"
              ]
            },
            {
              "id": "benefit",
              "description": "Explains the conservation benefit.",
              "any_of": [
                "reuses leftover water",
                "not discarded"
              ]
            },
            {
              "id": "boundary",
              "description": "States what must not be collected.",
              "any_of": [
                "food",
                "soap",
                "not go"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "labelled container",
            "clean outdoor floor",
            "reuses leftover water",
            "not discarded",
            "food",
            "soap",
            "not go"
          ],
          "model_answer": "Students can pour untouched leftover drinking water into a labelled container for cleaning the outdoor floor. This reuses water that would be discarded, but water mixed with food or soap should not go into the container.",
          "pass_score": 0.8
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "tank-conservation-paragraph-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Plan four boxes before writing: problem, action, because-reason, and any but-boundary.",
          "passage": "A family washes vegetables in a bowl and then pours the plain water onto balcony plants.",
          "prompt": "Explain why this is useful and when it would not be suitable.",
          "skill_ids": [
            "grammar.connectors_because_and_but",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "benefit",
              "description": "Explains the useful reuse.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "Names unsuitable contamination.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "benefit",
              "description": "Explains the useful reuse.",
              "any_of": [
                "rinse water",
                "plants",
                "saves fresh water"
              ]
            },
            {
              "id": "boundary",
              "description": "Names unsuitable contamination.",
              "any_of": [
                "salt",
                "detergent",
                "oil"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "rinse water",
            "plants",
            "saves fresh water",
            "salt",
            "detergent",
            "oil"
          ],
          "model_answer": "Reusing plain vegetable-rinse water on plants saves fresh water. However, water containing salt, detergent, or oil should not be used on the plants.",
          "pass_score": 0.8
        }
      }
    },
    {
      "level_id": "tank-inquiry-procedure",
      "title": "Use Facts, Then Build the Procedure",
      "focus": "select bounded source facts and arrange safe actions in order",
      "outcome": "Select relevant facts from a supplied packet and write a clear procedure with ordered actions, intended result, and explicit limits where evidence is missing.",
      "skill_ids": [
        "research.information_selection",
        "writing.procedure"
      ],
      "episode_kind": "application_mission",
      "source_anchor_ids": [
        "eng_c5_ch06:inquiry:12-14"
      ],
      "connect": {
        "teaching_block": "Inquiry combines evidence selection with procedure. A trustworthy response reports what the source packet says, puts actions in a usable order, and does not add safety results or success claims that the packet never gives.",
        "passage": "Packet: the north gutter is clear; the barrel has a lid; the outlet leaks. Procedure: isolate the barrel, repair and test the outlet, then reconnect the clear gutter.",
        "prompt": "Separate the supplied facts from the ordered actions, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "tank-inquiry-procedure-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
        "passage": "Fact card: The west roof supplies the largest gutter. The nursery needs water twice a week. The proposed barrel has a lid and tap.",
        "prompt": "Use the supplied facts to write a safe three-step collection procedure and its purpose.",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "invent a river beside the nursery",
          "west roof, clean lidded barrel, tap water for nursery",
          "leave the barrel open",
          "use facts unrelated to collection"
        ],
        "accepted_answers": [
          "west roof, clean lidded barrel, tap water for nursery"
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Inspection notes: inlet mesh torn; lid secure; overflow pipe clear; water contains leaves.",
          "prompt": "Write an inspection response that selects the relevant facts and orders the repair.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "evidence",
              "description": "Selects the fault and symptom.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "procedure",
              "description": "Orders the repair actions.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "selection",
              "description": "Separates relevant from sound parts.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "evidence",
              "description": "Selects the fault and symptom.",
              "any_of": [
                "torn mesh",
                "leaves"
              ]
            },
            {
              "id": "procedure",
              "description": "Orders the repair actions.",
              "any_of": [
                "stop inflow",
                "replace mesh",
                "remove leaves",
                "test"
              ]
            },
            {
              "id": "selection",
              "description": "Separates relevant from sound parts.",
              "any_of": [
                "lid secure",
                "overflow clear",
                "no repair"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "torn mesh",
            "leaves",
            "stop inflow",
            "replace mesh",
            "remove leaves",
            "test",
            "lid secure",
            "overflow clear"
          ],
          "model_answer": "The torn mesh is allowing leaves into the water. First stop new inflow, then replace the mesh, remove the leaves safely, and test the inlet again. The secure lid and clear overflow do not need repair now.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "evidence",
            "procedure",
            "selection"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Source packet: Clay pots cool by evaporation; covered steel drums reduce contamination; neither material removes dissolved salt.",
          "prompt": "Compare the supplied facts and propose one appropriate use without inventing a claim.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "facts",
              "description": "Reports both material facts accurately.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "use",
              "description": "Proposes a supported use.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Keeps the source boundary.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "facts",
              "description": "Reports both material facts accurately.",
              "any_of": [
                "clay cools",
                "steel reduces contamination"
              ]
            },
            {
              "id": "use",
              "description": "Proposes a supported use.",
              "any_of": [
                "protected storage",
                "cool small amount"
              ]
            },
            {
              "id": "limit",
              "description": "Keeps the source boundary.",
              "any_of": [
                "does not remove salt",
                "packet does not support"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "clay cools",
            "steel reduces contamination",
            "protected storage",
            "cool small amount",
            "does not remove salt",
            "packet does not support"
          ],
          "model_answer": "A covered steel drum is suitable for protected storage, while a clay pot may cool a small amount of water through evaporation. Neither should be described as removing dissolved salt because the packet does not support that claim.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "facts",
            "use",
            "limit"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Survey table: four classrooms report dripping taps; two report loose handles; one report includes both problems.",
          "prompt": "Write the order for verifying and responding to the survey without double-counting.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "selection",
              "description": "Uses the overlap fact correctly.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "steps",
              "description": "Orders verification and repair tracking.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "States the intended accurate outcome.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "selection",
              "description": "Uses the overlap fact correctly.",
              "any_of": [
                "one classroom both",
                "not double-count"
              ]
            },
            {
              "id": "steps",
              "description": "Orders verification and repair tracking.",
              "any_of": [
                "list once",
                "verify fault",
                "group repairs",
                "record completion"
              ]
            },
            {
              "id": "result",
              "description": "States the intended accurate outcome.",
              "any_of": [
                "accurate count",
                "repairs tracked"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "one classroom both",
            "not double-count",
            "list once",
            "verify fault",
            "group repairs",
            "record completion",
            "accurate count",
            "repairs tracked"
          ],
          "model_answer": "First list each classroom once, then verify whether it has a drip, a loose handle, or both. Next group repairs by fault and record completion. The classroom with both problems must not be counted as two separate rooms.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "selection",
            "steps",
            "result"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Safety note: A storage drum previously held paint. Cleaning by children is not permitted. It must be assessed by an authorised adult and may be rejected for water use.",
          "prompt": "Write a safe decision procedure using only these facts.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "prohibition",
              "description": "States what children must not do.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "authority",
              "description": "Names the required adult assessment.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Gives the bounded outcome.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "prohibition",
              "description": "States what children must not do.",
              "any_of": [
                "children not clean",
                "not use"
              ]
            },
            {
              "id": "authority",
              "description": "Names the required adult assessment.",
              "any_of": [
                "authorised adult",
                "inspect"
              ]
            },
            {
              "id": "decision",
              "description": "Gives the bounded outcome.",
              "any_of": [
                "reject",
                "safe non-drinking use",
                "local guidance"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "children not clean",
            "not use",
            "authorised adult",
            "inspect",
            "reject",
            "safe non-drinking use",
            "local guidance"
          ],
          "model_answer": "Do not ask children to clean or use the drum. An authorised adult must inspect its history and condition, then either reject it or approve only a safe non-drinking use under local guidance.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "prohibition",
            "authority",
            "decision"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Rain log: Monday 8 mm, Tuesday 0 mm, Wednesday 12 mm. Soil note: beds still damp on Thursday morning.",
          "prompt": "Select the relevant evidence and write a Thursday watering decision with a checking procedure.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "evidence",
              "description": "Selects recent rain and soil condition.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Makes a supported Thursday decision.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "procedure",
              "description": "Gives the next check and condition.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "evidence",
              "description": "Selects recent rain and soil condition.",
              "any_of": [
                "12 mm",
                "beds damp"
              ]
            },
            {
              "id": "decision",
              "description": "Makes a supported Thursday decision.",
              "any_of": [
                "delay watering"
              ]
            },
            {
              "id": "procedure",
              "description": "Gives the next check and condition.",
              "any_of": [
                "check below surface",
                "Friday",
                "dry near roots"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "12 mm",
            "beds damp",
            "delay watering",
            "check below surface",
            "Friday",
            "dry near roots"
          ],
          "model_answer": "Because the beds are still damp after recent rain, watering should be delayed. Check the soil below the surface on Friday; water only if it has become dry near the roots.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "evidence",
            "decision",
            "procedure"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Product notes: Container A has a food-grade label, lid, and tap. Container B has no label and a strong chemical smell.",
          "prompt": "Write a selection decision and the checks that must happen before use.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "selection",
              "description": "Chooses from supplied evidence.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "checks",
              "description": "Keeps pre-use checks.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "rejection",
              "description": "Explains why B is unsafe.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "selection",
              "description": "Chooses from supplied evidence.",
              "any_of": [
                "Container A",
                "food-grade",
                "lid",
                "tap"
              ]
            },
            {
              "id": "checks",
              "description": "Keeps pre-use checks.",
              "any_of": [
                "adult clean",
                "inspect"
              ]
            },
            {
              "id": "rejection",
              "description": "Explains why B is unsafe.",
              "any_of": [
                "unknown history",
                "chemical smell",
                "reject"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "Container A",
            "food-grade",
            "lid",
            "tap",
            "adult clean",
            "inspect",
            "unknown history",
            "chemical smell"
          ],
          "model_answer": "Container A is the only possible candidate because it is labelled food-grade and has a lid and tap. An adult must still clean and inspect it. Container B should be rejected because its history is unknown and it smells of chemicals.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "selection",
            "checks",
            "rejection"
          ]
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Poster brief: audience is Class 5; action is report leaks; location is the office desk; campaign runs 18-22 August.",
          "prompt": "Turn the fact packet into an accurate mini-poster message.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "action",
              "description": "States the campaign action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "details",
              "description": "Uses the supplied audience, place, and dates.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "purpose",
              "description": "Adds a supported purpose.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "action",
              "description": "States the campaign action.",
              "any_of": [
                "report leaks",
                "leak card"
              ]
            },
            {
              "id": "details",
              "description": "Uses the supplied audience, place, and dates.",
              "any_of": [
                "Class 5",
                "office desk",
                "18 to 22 August"
              ]
            },
            {
              "id": "purpose",
              "description": "Adds a supported purpose.",
              "any_of": [
                "repairs begin sooner"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "report leaks",
            "leak card",
            "Class 5",
            "office desk",
            "18 to 22 August",
            "repairs begin sooner"
          ],
          "model_answer": "REPORT LEAKS WITH A LEAK CARD. Class 5 learners can write the location on the leak card and submit it at the office desk from 18 to 22 August. Quick reporting helps repairs begin sooner.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "action",
            "details",
            "purpose"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Maintenance card: close valve; place warning sign; replace washer; reopen slowly; check for drips.",
          "prompt": "Write the procedure in order and explain why the warning sign belongs near the beginning.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "sequence",
              "description": "Uses all supplied actions in order.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "reason",
              "description": "Explains early warning.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "sequence",
              "description": "Uses all supplied actions in order.",
              "any_of": [
                "close valve",
                "warning sign",
                "replace washer",
                "reopen slowly",
                "check drips"
              ]
            },
            {
              "id": "reason",
              "description": "Explains early warning.",
              "any_of": [
                "tap unavailable",
                "people know"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 12,
          "relevance_terms": [
            "close valve",
            "warning sign",
            "replace washer",
            "reopen slowly",
            "check drips",
            "tap unavailable",
            "people know"
          ],
          "model_answer": "First close the valve and place a warning sign so people know the tap is unavailable. Replace the washer, reopen the valve slowly, and finally check for drips before removing the sign.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "sequence",
            "reason"
          ]
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "tank-inquiry-procedure-misconception",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "misconception": "The learner copies every fact, invents missing evidence, or gives actions without sequence, purpose, or safety boundaries.",
          "remediation": "Sort notes into relevant, irrelevant, and missing; then use first-next-final-result boxes and add an explicit 'needs checking' statement for every evidence gap.",
          "support_check_ids": [
            "tank-inquiry-procedure-bridge",
            "tank-inquiry-procedure-masterclass",
            "tank-inquiry-procedure-revision1",
            "tank-inquiry-procedure-revision2",
            "tank-inquiry-procedure-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Fact card: The west roof supplies the largest gutter. The nursery needs water twice a week. The proposed barrel has a lid and tap.",
          "prompt": "Use the supplied facts to write a safe three-step collection procedure and its purpose.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "source",
              "description": "Selects the relevant supplied location and need.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "steps",
              "description": "Gives ordered safe actions.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "purpose",
              "description": "States the intended result.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "source",
              "description": "Selects the relevant supplied location and need.",
              "any_of": [
                "west roof",
                "nursery twice a week"
              ]
            },
            {
              "id": "steps",
              "description": "Gives ordered safe actions.",
              "any_of": [
                "place barrel",
                "check inlet and lid",
                "use tap"
              ]
            },
            {
              "id": "purpose",
              "description": "States the intended result.",
              "any_of": [
                "store roof rain",
                "water nursery"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "west roof",
            "nursery twice a week",
            "place barrel",
            "check inlet and lid",
            "use tap",
            "store roof rain",
            "water nursery"
          ],
          "model_answer": "First place the lidded barrel at the west-roof gutter. Next check that the inlet and lid are clean. Finally use the tap twice a week to water the nursery; the aim is to store roof rain safely for plants.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "source",
            "steps",
            "purpose"
          ]
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Inspection notes: inlet mesh torn; lid secure; overflow pipe clear; water contains leaves.",
          "prompt": "Write an inspection response that selects the relevant facts and orders the repair.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "evidence",
              "description": "Selects the fault and symptom.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "procedure",
              "description": "Orders the repair actions.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "selection",
              "description": "Separates relevant from sound parts.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "evidence",
              "description": "Selects the fault and symptom.",
              "any_of": [
                "torn mesh",
                "leaves"
              ]
            },
            {
              "id": "procedure",
              "description": "Orders the repair actions.",
              "any_of": [
                "stop inflow",
                "replace mesh",
                "remove leaves",
                "test"
              ]
            },
            {
              "id": "selection",
              "description": "Separates relevant from sound parts.",
              "any_of": [
                "lid secure",
                "overflow clear",
                "no repair"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "torn mesh",
            "leaves",
            "stop inflow",
            "replace mesh",
            "remove leaves",
            "test",
            "lid secure",
            "overflow clear"
          ],
          "model_answer": "The torn mesh is allowing leaves into the water. First stop new inflow, then replace the mesh, remove the leaves safely, and test the inlet again. The secure lid and clear overflow do not need repair now.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "evidence",
            "procedure",
            "selection"
          ]
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Source packet: Clay pots cool by evaporation; covered steel drums reduce contamination; neither material removes dissolved salt.",
          "prompt": "Compare the supplied facts and propose one appropriate use without inventing a claim.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "facts",
              "description": "Reports both material facts accurately.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "use",
              "description": "Proposes a supported use.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Keeps the source boundary.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "facts",
              "description": "Reports both material facts accurately.",
              "any_of": [
                "clay cools",
                "steel reduces contamination"
              ]
            },
            {
              "id": "use",
              "description": "Proposes a supported use.",
              "any_of": [
                "protected storage",
                "cool small amount"
              ]
            },
            {
              "id": "limit",
              "description": "Keeps the source boundary.",
              "any_of": [
                "does not remove salt",
                "packet does not support"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "clay cools",
            "steel reduces contamination",
            "protected storage",
            "cool small amount",
            "does not remove salt",
            "packet does not support"
          ],
          "model_answer": "A covered steel drum is suitable for protected storage, while a clay pot may cool a small amount of water through evaporation. Neither should be described as removing dissolved salt because the packet does not support that claim.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "facts",
            "use",
            "limit"
          ]
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Survey table: four classrooms report dripping taps; two report loose handles; one report includes both problems.",
          "prompt": "Write the order for verifying and responding to the survey without double-counting.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "selection",
              "description": "Uses the overlap fact correctly.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "steps",
              "description": "Orders verification and repair tracking.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "result",
              "description": "States the intended accurate outcome.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "selection",
              "description": "Uses the overlap fact correctly.",
              "any_of": [
                "one classroom both",
                "not double-count"
              ]
            },
            {
              "id": "steps",
              "description": "Orders verification and repair tracking.",
              "any_of": [
                "list once",
                "verify fault",
                "group repairs",
                "record completion"
              ]
            },
            {
              "id": "result",
              "description": "States the intended accurate outcome.",
              "any_of": [
                "accurate count",
                "repairs tracked"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "one classroom both",
            "not double-count",
            "list once",
            "verify fault",
            "group repairs",
            "record completion",
            "accurate count",
            "repairs tracked"
          ],
          "model_answer": "First list each classroom once, then verify whether it has a drip, a loose handle, or both. Next group repairs by fault and record completion. The classroom with both problems must not be counted as two separate rooms.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "selection",
            "steps",
            "result"
          ]
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "tank-inquiry-procedure-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Highlight only supplied facts, order the actions, state the intended result, and mark any missing information instead of inventing it.",
          "passage": "Safety note: A storage drum previously held paint. Cleaning by children is not permitted. It must be assessed by an authorised adult and may be rejected for water use.",
          "prompt": "Write a safe decision procedure using only these facts.",
          "skill_ids": [
            "research.information_selection",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "prohibition",
              "description": "States what children must not do.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "authority",
              "description": "Names the required adult assessment.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Gives the bounded outcome.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "prohibition",
              "description": "States what children must not do.",
              "any_of": [
                "children not clean",
                "not use"
              ]
            },
            {
              "id": "authority",
              "description": "Names the required adult assessment.",
              "any_of": [
                "authorised adult",
                "inspect"
              ]
            },
            {
              "id": "decision",
              "description": "Gives the bounded outcome.",
              "any_of": [
                "reject",
                "safe non-drinking use",
                "local guidance"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "children not clean",
            "not use",
            "authorised adult",
            "inspect",
            "reject",
            "safe non-drinking use",
            "local guidance"
          ],
          "model_answer": "Do not ask children to clean or use the drum. An authorised adult must inspect its history and condition, then either reject it or approve only a safe non-drinking use under local guidance.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "prohibition",
            "authority",
            "decision"
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
        "activity_id": "eng_c5_ch06-assessment-tank-purpose-sequence-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A solar lantern charges in daylight, stores energy in a battery, and powers a lamp after sunset.",
        "prompt": "Transfer the sequence strategy: what happens between charging and lighting?",
        "skill_ids": [
          "reading.event_sequence",
          "reading.paragraph_main_idea"
        ],
        "options": [
          "the lamp stores sunlight on the roof",
          "energy is stored in the battery",
          "sunset charges the battery",
          "the lantern skips energy storage"
        ],
        "accepted_answers": [
          "energy is stored in the battery"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch06-assessment-tank-purpose-sequence-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Grain is cleaned, dried on mats, poured into sealed bins, and checked every week for moisture.",
        "prompt": "Which ordered summary preserves every important stage?",
        "skill_ids": [
          "reading.event_sequence",
          "reading.paragraph_main_idea"
        ],
        "options": [
          "seal, wet, clean, then ignore",
          "clean, dry, seal, then check",
          "check before the grain arrives",
          "dry only the storage bin"
        ],
        "accepted_answers": [
          "clean, dry, seal, then check"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-purpose-sequence-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A first-aid team checks the patient, cleans a small cut, covers it with a sterile pad, and records the treatment.",
        "prompt": "Why would recording come after covering the cut?",
        "skill_ids": [
          "reading.event_sequence",
          "reading.paragraph_main_idea"
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
              "care completed first",
              "record documents treatment"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "care completed first",
          "record documents treatment"
        ],
        "model_answer": "The immediate care is completed first, and the record then documents what treatment was given.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-purpose-sequence-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A compost bin receives vegetable peels, dry leaves are added, the mixture is turned weekly, and dark compost is used in soil.",
        "prompt": "Write the main process without losing the final purpose.",
        "skill_ids": [
          "reading.event_sequence",
          "reading.paragraph_main_idea"
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
              "scraps and leaves",
              "turned",
              "compost for soil"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "scraps and leaves",
          "turned",
          "compost for soil"
        ],
        "model_answer": "Kitchen scraps and dry leaves are mixed and turned until they become compost for the soil.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-purpose-sequence-5",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A covered tank does not create water; it protects water already collected and makes it available later.",
        "prompt": "What is the most accurate main idea?",
        "skill_ids": [
          "reading.event_sequence",
          "reading.paragraph_main_idea"
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
              "stores collected water",
              "later use",
              "does not create"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "stores collected water",
          "later use",
          "does not create"
        ],
        "model_answer": "A tank safely stores collected water for later use rather than producing new water.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-design-inference-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A library return box is painted like a giant book, while a sloped flap keeps rain away from returned books.",
        "prompt": "Transfer the identity-versus-function idea to this object.",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
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
              "book shape signals library",
              "flap keeps rain out"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "book shape signals library",
          "flap keeps rain out"
        ],
        "model_answer": "The book shape signals the library, while the sloped flap performs the practical job of keeping rain out.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-design-inference-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A vegetable cart has carrot pictures and a raised canopy. The pictures advertise the goods; the canopy shades them.",
        "prompt": "Which sentence separates symbolism from function correctly?",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
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
              "pictures communicate goods",
              "canopy protects"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "pictures communicate goods",
          "canopy protects"
        ],
        "model_answer": "Carrot pictures communicate what is sold, whereas the canopy physically protects the vegetables from sun.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-design-inference-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A bus stop has a route-map mural and a roof angled to drain rain behind the bench.",
        "prompt": "Explain which feature gives information and which manages weather.",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
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
              "mural gives route",
              "roof directs rain"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "mural gives route",
          "roof directs rain"
        ],
        "model_answer": "The mural gives route information, and the angled roof directs rain away from passengers.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-design-inference-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A clinic water cooler has a red cross sticker and a foot pedal. The sticker marks the clinic; the pedal lets users avoid touching the tap.",
        "prompt": "What is the strongest evidence-based interpretation?",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
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
              "sticker marks clinic",
              "pedal improves hygiene"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "sticker marks clinic",
          "pedal improves hygiene"
        ],
        "model_answer": "The sticker expresses place identity, while the pedal improves hygiene during use.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-design-inference-5",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Decorative features can tell a story about a person or place, but storage safety depends on covers, clean inlets, strong walls, and controlled outlets.",
        "prompt": "State the general principle in your own words.",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
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
              "decoration expresses identity",
              "practical features ensure safety"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "decoration expresses identity",
          "practical features ensure safety"
        ],
        "model_answer": "Decoration can express identity, while practical features determine whether a tank stores and releases water safely.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-contractions-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Asha cannot attend practice because she has not completed her project.",
        "prompt": "Transfer the contraction rule to this school sentence.",
        "skill_ids": [
          "grammar.sentence_order",
          "writing.complete_sentence"
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
              "can't attend",
              "hasn't completed"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "can't attend",
          "hasn't completed"
        ],
        "model_answer": "Asha can't attend practice because she hasn't completed her project.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-contractions-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The museum will not open until the guide is not busy.",
        "prompt": "Contract the verb groups without changing their tense.",
        "skill_ids": [
          "grammar.sentence_order",
          "writing.complete_sentence"
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
              "won't open",
              "isn't busy"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "won't open",
          "isn't busy"
        ],
        "model_answer": "The museum won't open until the guide isn't busy.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-contractions-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "We have not packed lunch because the bus has not arrived.",
        "prompt": "Write the contracted sentence in the same present-perfect meaning.",
        "skill_ids": [
          "grammar.sentence_order",
          "writing.complete_sentence"
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
              "haven't packed",
              "hasn't arrived"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "haven't packed",
          "hasn't arrived"
        ],
        "model_answer": "We haven't packed lunch because the bus hasn't arrived.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-contractions-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Priya would not enter the lab because she could not find her goggles.",
        "prompt": "Use two past conditional contractions accurately.",
        "skill_ids": [
          "grammar.sentence_order",
          "writing.complete_sentence"
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
              "wouldn't enter",
              "couldn't find"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "wouldn't enter",
          "couldn't find"
        ],
        "model_answer": "Priya wouldn't enter the lab because she couldn't find her goggles.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-contractions-5",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A contraction joins words and marks missing letters with an apostrophe; it does not change the original time or meaning.",
        "prompt": "Explain the rule and give one correct example from the sentence 'we are ready'.",
        "skill_ids": [
          "grammar.sentence_order",
          "writing.complete_sentence"
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
              "apostrophe",
              "omitted letters",
              "we're ready"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "apostrophe",
          "omitted letters",
          "we're ready"
        ],
        "model_answer": "A contraction uses an apostrophe for omitted letters without changing meaning; for example, 'we are ready' becomes 'we're ready'.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch06-assessment-tank-exclamation-emotion-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Yes! The final puzzle piece fits!",
        "prompt": "Transfer the emotion-reading strategy to this new setting.",
        "skill_ids": [
          "grammar.punctuation_capitalization",
          "reading.sentence_comprehension"
        ],
        "options": [
          "worry that a piece fits",
          "excitement at completing the puzzle",
          "sadness about finishing",
          "a neutral instruction to start"
        ],
        "accepted_answers": [
          "excitement at completing the puzzle"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch06-assessment-tank-exclamation-emotion-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Watch out! A bicycle is turning into the lane!",
        "prompt": "Which contextual detail justifies the urgent punctuation?",
        "skill_ids": [
          "grammar.punctuation_capitalization",
          "reading.sentence_comprehension"
        ],
        "options": [
          "the lane is always empty",
          "the bicycle stopped yesterday",
          "the speaker is describing a painting",
          "an approaching bicycle creates risk"
        ],
        "accepted_answers": [
          "an approaching bicycle creates risk"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-exclamation-emotion-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Amazing! The tiny seedling pushed through the hard soil.",
        "prompt": "Name the emotion and explain its cause.",
        "skill_ids": [
          "grammar.punctuation_capitalization",
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
              "wonder",
              "seedling",
              "hard soil"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "wonder",
          "seedling",
          "hard soil"
        ],
        "model_answer": "The speaker shows wonder because a delicate seedling managed to emerge through hard soil.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-exclamation-emotion-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Oh! I left the library book on the bus.",
        "prompt": "How does context change the likely meaning of 'Oh!' here?",
        "skill_ids": [
          "grammar.punctuation_capitalization",
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
              "sudden realisation",
              "concern",
              "forgotten book"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "sudden realisation",
          "concern",
          "forgotten book"
        ],
        "model_answer": "Here 'Oh!' signals sudden realisation and concern about the forgotten book.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-exclamation-emotion-5",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Exclamation marks can signal joy, fear, surprise, warning, or admiration; the surrounding event tells us which feeling fits.",
        "prompt": "State the rule for interpreting an exclamation.",
        "skill_ids": [
          "grammar.punctuation_capitalization",
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
              "surrounding event",
              "infer emotion",
              "punctuation alone"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "surrounding event",
          "infer emotion",
          "punctuation alone"
        ],
        "model_answer": "Use the surrounding event and words to infer the specific emotion; punctuation alone does not name it.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch06-assessment-tank-animal-word-meaning-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "In a theatre notice, 'cast' means the group of performers. In a fishing note, 'cast' means to throw a line.",
        "prompt": "Transfer the context strategy: what does 'cast' mean in 'The cast bowed after the play'?",
        "skill_ids": [
          "vocab.chapter_word_usage",
          "reading.word_meaning_context"
        ],
        "options": [
          "throw a fishing line",
          "a hard covering for an arm",
          "the group of performers",
          "a young animal"
        ],
        "accepted_answers": [
          "the group of performers"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch06-assessment-tank-animal-word-meaning-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A crane lifted a pipe at the building site. A crane also names a long-legged bird.",
        "prompt": "Which clue fixes the meaning in this sentence?",
        "skill_ids": [
          "vocab.chapter_word_usage",
          "reading.word_meaning_context"
        ],
        "options": [
          "the word always means a bird",
          "the pipe is a young crane",
          "no clue can distinguish meanings",
          "the lifting action at a building site"
        ],
        "accepted_answers": [
          "the lifting action at a building site"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-animal-word-meaning-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The word 'seal' may name a sea animal or the act of closing something tightly.",
        "prompt": "What does it mean in 'Workers seal the tank wall'?",
        "skill_ids": [
          "vocab.chapter_word_usage",
          "reading.word_meaning_context"
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
              "close tightly",
              "tank wall",
              "prevent leak"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "close tightly",
          "tank wall",
          "prevent leak"
        ],
        "model_answer": "It means to close the tank wall tightly so water cannot leak.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-animal-word-meaning-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A doe and her fawn crossed the clearing before a herd of deer followed.",
        "prompt": "Identify the adult female, the young animal, and the group word.",
        "skill_ids": [
          "vocab.chapter_word_usage",
          "reading.word_meaning_context"
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
              "doe adult female",
              "fawn young",
              "herd group"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "doe adult female",
          "fawn young",
          "herd group"
        ],
        "model_answer": "The doe is the adult female, the fawn is the young deer, and the herd is the group.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-conservation-paragraph-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A computer lab wants to reduce electricity use. Monitors are often left on during lunch although no one is working.",
        "prompt": "Transfer the conservation paragraph structure to energy use.",
        "skill_ids": [
          "grammar.connectors_because_and_but",
          "writing.paragraph"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "problem",
            "description": "Names the waste.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "action",
            "description": "Gives a practical action.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "reason",
            "description": "Explains the benefit.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "problem",
            "description": "Names the waste.",
            "any_of": [
              "monitors left on",
              "during lunch"
            ]
          },
          {
            "id": "action",
            "description": "Gives a practical action.",
            "any_of": [
              "switch monitors off",
              "door reminder"
            ]
          },
          {
            "id": "reason",
            "description": "Explains the benefit.",
            "any_of": [
              "reduces electricity",
              "no one using"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "monitors left on",
          "during lunch",
          "switch monitors off",
          "door reminder",
          "reduces electricity",
          "no one using"
        ],
        "model_answer": "The lab should switch monitors off during lunch because no one is using them. This reduces unnecessary electricity use, while a reminder beside the door can help the last student check each row.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-conservation-paragraph-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A canteen throws away edible fruit because slightly marked pieces are not displayed. Safe pieces could be trimmed and used promptly in fruit salad.",
        "prompt": "Write a balanced waste-reduction recommendation with a safety condition.",
        "skill_ids": [
          "grammar.connectors_because_and_but",
          "writing.paragraph"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "recommendation",
            "description": "States the safe reuse.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "benefit",
            "description": "Explains reduced waste.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "condition",
            "description": "Keeps the safety boundary.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "recommendation",
            "description": "States the safe reuse.",
            "any_of": [
              "trim safe fruit",
              "fruit salad"
            ]
          },
          {
            "id": "benefit",
            "description": "Explains reduced waste.",
            "any_of": [
              "reduces food waste"
            ]
          },
          {
            "id": "condition",
            "description": "Keeps the safety boundary.",
            "any_of": [
              "spoiled fruit discarded",
              "hygiene rules"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "trim safe fruit",
          "fruit salad",
          "reduces food waste",
          "spoiled fruit discarded",
          "hygiene rules"
        ],
        "model_answer": "The canteen can trim safe, slightly marked fruit and use it promptly in fruit salad, which reduces food waste. However, spoiled or unsafe fruit must still be discarded according to hygiene rules.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-conservation-paragraph-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A classroom prints every draft on a new sheet. Students can review digitally or use the blank back of non-confidential pages.",
        "prompt": "Develop a paragraph comparing the current habit with two better choices.",
        "skill_ids": [
          "grammar.connectors_because_and_but",
          "writing.paragraph"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "problem",
            "description": "Names the wasteful habit.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "choices",
            "description": "Gives two suitable alternatives.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "benefit",
            "description": "Explains the result.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "problem",
            "description": "Names the wasteful habit.",
            "any_of": [
              "fresh sheet",
              "wastes paper"
            ]
          },
          {
            "id": "choices",
            "description": "Gives two suitable alternatives.",
            "any_of": [
              "review digitally",
              "blank backs"
            ]
          },
          {
            "id": "benefit",
            "description": "Explains the result.",
            "any_of": [
              "reduce new paper",
              "less demand"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "fresh sheet",
          "wastes paper",
          "review digitally",
          "blank backs",
          "reduce new paper",
          "less demand"
        ],
        "model_answer": "Printing each draft on a fresh sheet wastes paper. Students can review suitable drafts digitally, and they can use the blank backs of non-confidential pages for rough work. These choices reduce demand for new paper.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-conservation-paragraph-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A bus driver keeps the engine running for twenty minutes while waiting at an empty stop. The route rule allows switching off during long safe waits.",
        "prompt": "Use the conservation structure to recommend an action and explain a condition.",
        "skill_ids": [
          "grammar.connectors_because_and_but",
          "writing.paragraph"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "action",
            "description": "States the recommended action.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "reason",
            "description": "Explains the benefit.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "condition",
            "description": "States the safety boundary.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "action",
            "description": "States the recommended action.",
            "any_of": [
              "switch off engine",
              "long safe wait"
            ]
          },
          {
            "id": "reason",
            "description": "Explains the benefit.",
            "any_of": [
              "saves fuel",
              "reduces pollution"
            ]
          },
          {
            "id": "condition",
            "description": "States the safety boundary.",
            "any_of": [
              "safety rule",
              "operating rule"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "switch off engine",
          "long safe wait",
          "saves fuel",
          "reduces pollution",
          "safety rule",
          "operating rule"
        ],
        "model_answer": "The driver should switch off the engine during a long safe wait because idling wastes fuel and adds pollution. The engine should remain on only when a safety or operating rule genuinely requires it.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-inquiry-procedure-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Library packet: books are sorted by return date, damaged covers are flagged, and then books are shelved by call number.",
        "prompt": "Transfer the information-selection and procedure skill to the library.",
        "skill_ids": [
          "research.information_selection",
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "steps",
            "description": "Reports the supplied order.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "purpose",
            "description": "Explains the separation.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "steps",
            "description": "Reports the supplied order.",
            "any_of": [
              "sort by date",
              "flag damage",
              "shelve by call number"
            ]
          },
          {
            "id": "purpose",
            "description": "Explains the separation.",
            "any_of": [
              "damage records",
              "reshelving"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 12,
        "relevance_terms": [
          "sort by date",
          "flag damage",
          "shelve by call number",
          "damage records",
          "reshelving"
        ],
        "model_answer": "First sort returned books by date, then flag any damaged covers for repair, and finally shelve sound books by call number. The process keeps damage records separate from normal reshelving.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-inquiry-procedure-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Science packet: Seed A receives light and water; Seed B receives water but no light; both are the same kind and planted in equal soil.",
        "prompt": "Write a fair observation procedure without claiming a result before the test.",
        "skill_ids": [
          "research.information_selection",
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "controls",
            "description": "Keeps supplied fair conditions.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "procedure",
            "description": "Gives repeatable observation steps.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "limit",
            "description": "Avoids invented results.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "controls",
            "description": "Keeps supplied fair conditions.",
            "any_of": [
              "equal water",
              "same kind",
              "equal soil"
            ]
          },
          {
            "id": "procedure",
            "description": "Gives repeatable observation steps.",
            "any_of": [
              "assigned light",
              "record growth",
              "same time"
            ]
          },
          {
            "id": "limit",
            "description": "Avoids invented results.",
            "any_of": [
              "do not claim result",
              "until observations"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "equal water",
          "same kind",
          "equal soil",
          "assigned light",
          "record growth",
          "same time",
          "do not claim result",
          "until observations"
        ],
        "model_answer": "Place both pots in their assigned conditions, give equal amounts of water, and record growth at the same time each day. Do not predict that either seed will grow better until observations provide evidence.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-inquiry-procedure-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Travel facts: Bus 14 leaves at 8:10, stops at the museum gate, and returns at 1:30. Students must carry water and an identity card.",
        "prompt": "Write a concise trip procedure using every relevant fact.",
        "skill_ids": [
          "research.information_selection",
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "preparation",
            "description": "Includes required items.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "travel",
            "description": "Uses bus, time, and stop.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "return",
            "description": "Includes the return time.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "preparation",
            "description": "Includes required items.",
            "any_of": [
              "water",
              "identity card"
            ]
          },
          {
            "id": "travel",
            "description": "Uses bus, time, and stop.",
            "any_of": [
              "Bus 14",
              "8:10",
              "museum gate"
            ]
          },
          {
            "id": "return",
            "description": "Includes the return time.",
            "any_of": [
              "1:30",
              "with group"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "water",
          "identity card",
          "Bus 14",
          "8:10",
          "museum gate",
          "1:30",
          "with group"
        ],
        "model_answer": "Carry water and an identity card, reach Bus 14 before 8:10, get off at the museum gate, and return with the group at 1:30. The steps keep the supplied travel details clear.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch06-assessment-tank-inquiry-procedure-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Recipe card: rinse one cup of lentils; add three cups of water; simmer until soft; add salt after cooking.",
        "prompt": "Write the procedure without changing quantities or sequence.",
        "skill_ids": [
          "research.information_selection",
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "materials",
            "description": "Keeps the supplied quantities.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "steps",
            "description": "Preserves the sequence.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "materials",
            "description": "Keeps the supplied quantities.",
            "any_of": [
              "one cup lentils",
              "three cups water"
            ]
          },
          {
            "id": "steps",
            "description": "Preserves the sequence.",
            "any_of": [
              "rinse",
              "add water",
              "simmer",
              "salt after"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 12,
        "relevance_terms": [
          "one cup lentils",
          "three cups water",
          "rinse",
          "add water",
          "simmer",
          "salt after"
        ],
        "model_answer": "First rinse one cup of lentils. Add three cups of water and simmer until the lentils are soft. Add salt only after cooking, as the card directs.",
        "pass_score": 0.8
      }
    ],
    "strands": [
      {
        "strand_id": "tank-purpose-sequence",
        "skill_ids": [
          "reading.event_sequence",
          "reading.paragraph_main_idea"
        ],
        "minimum_items": 5,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "tank-purpose-sequence"
        ]
      },
      {
        "strand_id": "tank-design-inference",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
        ],
        "minimum_items": 5,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "tank-design-inference"
        ]
      },
      {
        "strand_id": "tank-contractions",
        "skill_ids": [
          "grammar.sentence_order",
          "writing.complete_sentence"
        ],
        "minimum_items": 5,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "tank-contractions"
        ]
      },
      {
        "strand_id": "tank-exclamation-emotion",
        "skill_ids": [
          "grammar.punctuation_capitalization",
          "reading.sentence_comprehension"
        ],
        "minimum_items": 5,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "tank-exclamation-emotion"
        ]
      },
      {
        "strand_id": "tank-animal-word-meaning",
        "skill_ids": [
          "vocab.chapter_word_usage",
          "reading.word_meaning_context"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "tank-animal-word-meaning"
        ]
      },
      {
        "strand_id": "tank-conservation-paragraph",
        "skill_ids": [
          "grammar.connectors_because_and_but",
          "writing.paragraph"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "tank-conservation-paragraph"
        ]
      },
      {
        "strand_id": "tank-inquiry-procedure",
        "skill_ids": [
          "research.information_selection",
          "writing.procedure"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "tank-inquiry-procedure"
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
    "tank-purpose-sequence": "Follow the same water or object through each action, then compress the chain into its central purpose.",
    "tank-design-inference": "Separate a feature's practical job from the identity or beauty communicated by its decoration.",
    "tank-contractions": "Expand the joined words first, preserve their order and meaning, then rebuild the complete sentence.",
    "tank-exclamation-emotion": "Use the words and situation to identify the feeling before choosing capitals and end punctuation.",
    "tank-animal-word-meaning": "Use relationship and action clues to distinguish an animal, its young, and its group in context.",
    "tank-conservation-paragraph": "Name a concrete problem, recommend a feasible action, and connect the action to a measurable benefit or limit.",
    "tank-inquiry-procedure": "Select only supplied facts, place safe actions in executable order, and state the decision boundary.",
}


_DEPTH = {
    "tank-purpose-sequence": {
        "guided": [
            _one(
                "Rain from the music-room roof enters a gutter, passes through a leaf screen, and collects in a blue drum beside the garden.",
                "Retell the three water movements in order.",
                "The rain enters the gutter, passes through the leaf screen, and finally collects in the blue garden drum.",
                "enters the gutter, passes through the leaf screen, and finally collects",
                description="States all three water movements in order.",
                skills=["reading.event_sequence"],
            ),
            _one(
                "A caretaker fills a clay basin at dawn. Birds drink from it through the hot afternoon, and she washes and refills it at sunset.",
                "State the main idea without listing unrelated time details.",
                "The caretaker keeps a clean basin available so birds can drink safely throughout the day.",
                "keeps a clean basin available so birds can drink safely",
                description="States the central purpose of the repeated actions.",
                skills=["reading.paragraph_main_idea"],
            ),
        ],
        "independent": [
            _two(
                "A nursery worker opens the tank valve, sends water into a narrow channel, closes the valve when the channel reaches the last bed, and covers the tank again. The seedlings receive water without flooding the path.",
                "Write the action chain and explain its main purpose in two or three sentences.",
                "The worker opens the valve, guides water through the channel to the last bed, then closes and covers the tank. This controlled sequence waters the seedlings without flooding the path.",
                ("order", "Preserves the valve, channel, closing, and covering sequence.", "opens the valve, guides water through the channel to the last bed, then closes and covers the tank"),
                ("purpose", "States why the sequence matters.", "waters the seedlings without flooding the path"),
                skills=["reading.event_sequence", "reading.paragraph_main_idea"],
                min_words=22,
                ordered=True,
            ),
            _two(
                "At a health camp, sealed water cans arrive at the gate. Volunteers check each seal, carry approved cans to the drinking station, and return empty cans to a marked rack for collection.",
                "Summarise the route in order and state the organising idea.",
                "Sealed cans are checked at the gate, approved cans move to the drinking station, and empties return to the marked rack. The system keeps safe drinking water and used containers organised.",
                ("route", "Sequences checking, delivery, and return.", "checked at the gate, approved cans move to the drinking station, and empties return to the marked rack"),
                ("idea", "Explains the organising purpose.", "keeps safe drinking water and used containers organised"),
                skills=["reading.event_sequence", "reading.paragraph_main_idea"],
                min_words=24,
                ordered=True,
            ),
        ],
        "transfer": [
            _two(
                "A science group places a rain gauge in an open corner, reads the level after each shower, records the number in a table, and empties the gauge before the next reading.",
                "Explain the correct sequence and why the final action is necessary.",
                "The group places the gauge, reads and records each rainfall level, then empties it before the next shower. Emptying resets the gauge so the next reading measures only new rain.",
                ("sequence", "Orders placement, reading, recording, and emptying.", "places the gauge, reads and records each rainfall level, then empties it"),
                ("reason", "Explains why the gauge is emptied.", "the next reading measures only new rain"),
                skills=["reading.event_sequence", "reading.paragraph_main_idea"],
                min_words=22,
                ordered=True,
            ),
        ],
        "support": [
            _one(
                "Water leaves a hand pump, fills a steel pail, and is poured into a covered kitchen pot.",
                "Say where the water goes first, next, and last.",
                "First the water leaves the hand pump, next it fills the pail, and last it enters the covered pot.",
                "leaves the hand pump, next it fills the pail, and last it enters the covered pot",
                description="Uses first, next, and last for the complete route.",
                skills=["reading.event_sequence"],
            ),
            _two(
                "A school tray catches water dripping from washed lunch boxes. A monitor carries the tray to the herb patch and pours it around the roots.",
                "Build the two-step route and its purpose.",
                "The tray catches the drips, and the monitor carries them to the herb roots. The route reuses clean leftover water for plants.",
                ("route", "States collection followed by carrying.", "tray catches the drips, and the monitor carries them to the herb roots"),
                ("purpose", "States the reuse purpose.", "reuses clean leftover water for plants"),
                skills=["reading.event_sequence", "reading.paragraph_main_idea"],
            ),
            _one(
                "A tanker fills the community tank before sunrise. Families collect small amounts during fixed hours so the supply lasts until evening.",
                "What is the central idea of the two actions?",
                "Timed collection helps the shared tanker supply last for the whole community until evening.",
                "Timed collection helps the shared tanker supply last",
                description="Connects controlled collection with a lasting shared supply.",
                skills=["reading.paragraph_main_idea"],
            ),
            _two(
                "A bottle is rinsed, filled at the cooler, labelled with the learner's name, and placed upright in a shaded crate.",
                "Retell the order and explain why the last location matters.",
                "The bottle is rinsed, filled, labelled, and then placed upright in the shaded crate. The final position keeps it protected and easy to identify.",
                ("order", "Preserves all four actions.", "rinsed, filled, labelled, and then placed upright"),
                ("reason", "Explains the final position.", "keeps it protected and easy to identify"),
                skills=["reading.event_sequence", "reading.paragraph_main_idea"],
                ordered=True,
            ),
            _one(
                "Roof water reaches a filter box before entering a storage tank. The filter catches leaves so the inlet does not clog.",
                "State the main job of the filter in this route.",
                "The filter removes leaves before storage and protects the tank inlet from clogging.",
                "protects the tank inlet from clogging",
                description="States the filter's central job in the route.",
                skills=["reading.paragraph_main_idea"],
            ),
        ],
    },
    "tank-design-inference": {
        "guided": [
            _one(
                "A public tap has a broad stone base that catches splashes and a painted lotus above it that marks the neighbourhood garden group.",
                "Explain which feature has a practical job and which communicates identity.",
                "The broad base catches splashes, while the painted lotus identifies the neighbourhood garden group.",
                "broad base catches splashes, while the painted lotus identifies the neighbourhood garden group",
                description="Distinguishes practical function from identity.",
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
            _one(
                "A grain bin has a tight lid and blue wave patterns around its side. The lid blocks insects; the waves match the cooperative's logo.",
                "Why should the lid and waves not be given the same purpose?",
                "The lid protects the grain from insects, but the wave pattern only shows the cooperative's identity.",
                "lid protects the grain from insects, but the wave pattern only shows the cooperative's identity",
                description="Uses the stated evidence to separate both purposes.",
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
        ],
        "independent": [
            _two(
                "A roadside water kiosk has a sloping roof, a raised platform, and a painted camel on the front. During rain, water runs off the roof; the platform keeps containers above mud; the camel is the local trust's emblem.",
                "Explain two practical features and the separate role of the camel image.",
                "The sloping roof carries rain away and the platform keeps containers above mud. The camel image identifies the local trust rather than controlling water.",
                ("function", "Explains both practical design features.", "sloping roof carries rain away and the platform keeps containers above mud"),
                ("identity", "Explains the emblem without inventing a function.", "camel image identifies the local trust rather than controlling water"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=23,
            ),
            _two(
                "An earthen tank has a narrow covered opening, a low tap, and carved fish along the outer wall. The opening reduces falling dust, the tap releases water near ground level, and the fish refer to the potters who built it.",
                "Infer why the opening and tap are useful, then interpret the carving.",
                "The covered opening reduces dust and the low tap makes water easier to release into a vessel. The carved fish honour the potters and do not filter the stored water.",
                ("utility", "Explains the opening and tap from supplied clues.", "covered opening reduces dust and the low tap makes water easier to release"),
                ("symbol", "Keeps the carving's role symbolic.", "carved fish honour the potters and do not filter the stored water"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=24,
            ),
        ],
        "transfer": [
            _two(
                "A library return box has a weatherproof flap and a mural of open books. The flap stops rain entering the slot; the mural helps visitors recognise the literacy campaign.",
                "Transfer the design-versus-identity distinction to this object.",
                "The weatherproof flap performs the practical job of blocking rain, while the open-book mural identifies the literacy campaign.",
                ("practical", "Names the flap's physical function.", "flap performs the practical job of blocking rain"),
                ("identity", "Names the mural's communication role.", "mural identifies the literacy campaign"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
        ],
        "support": [
            _one(
                "A lunch carrier has a locking clip and a sticker showing the owner's initials.",
                "Which part prevents opening, and which part identifies the owner?",
                "The locking clip prevents the carrier from opening, while the initials identify its owner.",
                "locking clip prevents the carrier from opening, while the initials identify its owner",
                description="Separates a working part from an identity mark.",
                skills=["reading.inference_reason"],
            ),
            _two(
                "A bicycle helmet has a hard shell, air vents, and a painted team stripe. The shell absorbs impact, the vents release heat, and the stripe matches the cycling club.",
                "Sort the three features into protection, comfort, and identity.",
                "The hard shell provides protection and the vents improve comfort. The painted stripe communicates the cycling club's identity.",
                ("functions", "Explains protection and comfort.", "hard shell provides protection and the vents improve comfort"),
                ("identity", "Explains the painted stripe.", "painted stripe communicates the cycling club's identity"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
            _one(
                "A seed box has drainage holes underneath and a sunflower drawn on its side. Water leaves through the holes; the drawing labels the gardening team.",
                "Give one evidence-based sentence about both roles.",
                "The holes drain extra water, whereas the sunflower drawing labels the gardening team.",
                "holes drain extra water, whereas the sunflower drawing labels the gardening team",
                description="Contrasts the physical and identifying roles.",
                skills=["writing.reason_answer"],
            ),
            _two(
                "A shaded bus stop has a deep roof, a bench, and a peacock symbol on the route panel. The roof blocks sun, the bench supports waiting passengers, and the symbol marks the city line.",
                "Explain the two useful features before interpreting the symbol.",
                "The deep roof gives shade and the bench supports passengers while they wait. The peacock symbol marks the city bus line.",
                ("use", "Explains roof and bench utility.", "deep roof gives shade and the bench supports passengers"),
                ("mark", "Explains the route symbol.", "peacock symbol marks the city bus line"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
            _one(
                "A medicine cabinet has a childproof latch and a red cross printed outside. The latch restricts opening; the cross signals first-aid storage.",
                "Why would removing the printed cross not weaken the latch?",
                "The red cross only signals first-aid storage, while the separate childproof latch controls opening.",
                "red cross only signals first-aid storage, while the separate childproof latch controls opening",
                description="Explains that symbol and mechanism have independent roles.",
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
        ],
    },
    "tank-contractions": {
        "guided": [
            _one(
                "The notice says, 'We aren't filling bottles after the final bell.'",
                "Expand the contraction and keep the sentence meaning unchanged.",
                "The expanded sentence is: We are not filling bottles after the final bell.",
                "We are not filling bottles after the final bell",
                description="Expands aren't without changing word order or meaning.",
                skills=["grammar.sentence_order", "writing.complete_sentence"],
            ),
            _one(
                "Mina says, 'I'll close the tap when the bucket reaches the mark.'",
                "Rewrite the sentence with the joined words expanded.",
                "Mina says, 'I will close the tap when the bucket reaches the mark.'",
                "I will close the tap when the bucket reaches the mark",
                description="Expands I'll into a complete grammatical sentence.",
                skills=["grammar.sentence_order", "writing.complete_sentence"],
            ),
        ],
        "independent": [
            _two(
                "Draft: 'They've checked the lid, but they haven't cleaned the outlet.'",
                "Expand both contractions and explain what has and has not happened.",
                "They have checked the lid, but they have not cleaned the outlet. The lid check is complete, while outlet cleaning is still unfinished.",
                ("expansion", "Expands both contractions accurately.", "They have checked the lid, but they have not cleaned the outlet"),
                ("meaning", "Preserves the contrast between completed and unfinished work.", "lid check is complete, while outlet cleaning is still unfinished"),
                skills=["grammar.sentence_order", "writing.complete_sentence"],
                min_words=20,
            ),
            _two(
                "Message: 'Ravi couldn't lift the drum, so we'll bring a trolley.'",
                "Write the full forms and preserve the cause-and-response order.",
                "Ravi could not lift the drum, so we will bring a trolley. His difficulty comes first and the planned response follows.",
                ("forms", "Expands couldn't and we'll.", "Ravi could not lift the drum, so we will bring a trolley"),
                ("order", "Preserves cause before response.", "difficulty comes first and the planned response follows"),
                skills=["grammar.sentence_order", "writing.complete_sentence"],
                min_words=18,
                ordered=True,
            ),
        ],
        "transfer": [
            _two(
                "Workshop note: 'The wheel isn't turning because it's caught on the rope.'",
                "Expand the contractions and retain the stated cause.",
                "The wheel is not turning because it is caught on the rope. The rope remains the stated cause of the blocked movement.",
                ("sentence", "Expands both joined forms.", "wheel is not turning because it is caught on the rope"),
                ("cause", "Keeps the rope as the cause.", "rope remains the stated cause"),
                skills=["grammar.sentence_order", "writing.complete_sentence"],
            ),
        ],
        "support": [
            _one(
                "Sentence: 'She doesn't waste drinking water.'",
                "Replace the contraction with its two full words.",
                "She does not waste drinking water.",
                "She does not waste drinking water",
                description="Expands doesn't correctly.",
                skills=["writing.complete_sentence"],
                min_words=6,
            ),
            _one(
                "Sentence: 'We're measuring the tank this afternoon.'",
                "Expand We're and keep the time phrase in place.",
                "We are measuring the tank this afternoon.",
                "We are measuring the tank this afternoon",
                description="Expands We're while preserving the sentence.",
                skills=["grammar.sentence_order", "writing.complete_sentence"],
                min_words=7,
            ),
            _one(
                "Sentence: 'You shouldn't lean over the open well.'",
                "Write the complete negative advice.",
                "You should not lean over the open well. This complete sentence preserves the negative safety advice.",
                "You should not lean over the open well",
                description="Expands shouldn't into safe complete advice.",
                skills=["writing.complete_sentence"],
                min_words=8,
            ),
            _one(
                "Sentence: 'I'd report the broken handle before use.' Here I'd means I would.",
                "Rewrite the whole sentence without the contraction.",
                "I would report the broken handle before use.",
                "I would report the broken handle before use",
                description="Uses the supplied full form in correct order.",
                skills=["grammar.sentence_order", "writing.complete_sentence"],
                min_words=8,
            ),
            _two(
                "Pair: 'It hasn't rained, so we can't delay watering.'",
                "Expand both joined forms and keep the conclusion after the reason.",
                "It has not rained, so we cannot delay watering. The lack of rain remains the reason for watering now.",
                ("forms", "Expands hasn't and can't.", "It has not rained, so we cannot delay watering"),
                ("meaning", "Preserves the reason for the decision.", "lack of rain remains the reason for watering now"),
                skills=["grammar.sentence_order", "writing.complete_sentence"],
            ),
        ],
    },
    "tank-exclamation-emotion": {
        "guided": [
            _one(
                "A child sees water spilling toward an electric socket and calls out, 'stop the pump now'",
                "Rewrite the warning with correct capitalization and punctuation.",
                "Stop the pump now! This urgent warning signals immediate danger.",
                "Stop the pump now!",
                description="Produces a capitalized urgent warning with an exclamation mark.",
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=6,
            ),
            _one(
                "After weeks of repairs, the first clean stream reaches the village tap. Leela says, 'what wonderful news'",
                "Punctuate the sentence to match Leela's joy.",
                "What wonderful news! The exclamation expresses joyful surprise.",
                "What wonderful news!",
                description="Uses capitals and punctuation that express joy.",
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=6,
            ),
        ],
        "independent": [
            _two(
                "During inspection, Farah notices a crack widening beside the tank outlet. Her draft is: 'look out the wall is giving way'",
                "Rewrite the line and explain the emotion shown by your punctuation.",
                "Look out! The wall is giving way! The exclamation marks show Farah's urgent alarm about immediate danger.",
                ("line", "Corrects capitals and end punctuation.", "Look out! The wall is giving way!"),
                ("emotion", "Names urgent alarm and links it to danger.", "urgent alarm about immediate danger"),
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=16,
            ),
            _two(
                "A repaired hand pump works after months of failure. The mechanic smiles and says, 'at last it works'",
                "Punctuate the speech and state the feeling supported by the scene.",
                "At last, it works! The words and exclamation mark express relief and satisfaction after the long repair.",
                ("speech", "Capitalizes and punctuates the spoken line.", "At last, it works!"),
                ("feeling", "Infers relief from the completed repair.", "express relief and satisfaction after the long repair"),
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=16,
            ),
        ],
        "transfer": [
            _two(
                "At a football match, a loose goalpost begins to fall. A coach shouts, 'move away from the post'",
                "Correct the warning and explain why an exclamation mark fits.",
                "Move away from the post! The exclamation mark fits because the coach is giving an urgent safety command.",
                ("warning", "Writes the correctly punctuated command.", "Move away from the post!"),
                ("reason", "Connects punctuation to urgent safety.", "giving an urgent safety command"),
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
            ),
        ],
        "support": [
            _one(
                "Draft warning: 'careful the floor is wet'",
                "Add the capital letter and punctuation needed for an urgent warning.",
                "Careful! The floor is wet! This warning signals an immediate slipping risk.",
                "Careful! The floor is wet!",
                description="Produces the complete urgent warning.",
                skills=["grammar.punctuation_capitalization"],
                min_words=6,
            ),
            _two(
                "Nitin opens a surprise parcel and says, 'this is exactly the tool we needed'",
                "Correct the line and identify the supported feeling.",
                "This is exactly the tool we needed! Nitin's words show delighted surprise.",
                ("line", "Corrects the spoken sentence.", "This is exactly the tool we needed!"),
                ("feeling", "Names delighted surprise.", "show delighted surprise"),
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=10,
            ),
            _one(
                "A sign beside a fragile pipe reads, 'do not step here'",
                "Rewrite the safety command correctly.",
                "Do not step here! This direct command gives an urgent safety warning.",
                "Do not step here!",
                description="Capitalizes and punctuates the safety command.",
                skills=["grammar.punctuation_capitalization"],
                min_words=6,
            ),
            _two(
                "The rain finally reaches a dry farm. A farmer calls, 'the pond is filling again'",
                "Punctuate the call and explain the emotion from the context.",
                "The pond is filling again! The farmer feels hopeful relief after the dry period.",
                ("call", "Corrects the exclamation.", "The pond is filling again!"),
                ("emotion", "Uses the dry-period clue.", "feels hopeful relief after the dry period"),
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
            ),
            _one(
                "Draft: 'oh no the bucket has split'",
                "Show shock with correct capitals and punctuation.",
                "Oh no! The bucket has split!",
                "Oh no! The bucket has split!",
                description="Writes a correctly punctuated expression of shock.",
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=6,
            ),
        ],
    },
    "tank-animal-word-meaning": {
        "guided": [
            _one(
                "A mare stood beside her foal while the herd moved slowly across the grassland.",
                "Use the relationship clues to explain mare, foal, and herd.",
                "A mare is an adult female horse, a foal is a young horse, and a herd is the larger group moving together.",
                "mare is an adult female horse, a foal is a young horse, and a herd is the larger group",
                description="Explains the adult, young, and group terms.",
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
            ),
            _one(
                "The ewe called softly, and her lamb returned from the flock grazing near the fence.",
                "Infer the meaning of ewe, lamb, and flock from the sentence.",
                "The ewe is the adult female sheep, the lamb is her young, and the flock is the group of sheep.",
                "ewe is the adult female sheep, the lamb is her young, and the flock is the group",
                description="Uses context to map all three relationship words.",
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
            ),
        ],
        "independent": [
            _two(
                "A sow guided two piglets away from the gate while the rest of the sounder searched the soil under the trees.",
                "Define the three animal terms and cite the action clue for piglets.",
                "A sow is an adult female pig, piglets are young pigs, and a sounder is a group of pigs. The sow guiding them away from the gate shows that the piglets are the young animals.",
                ("terms", "Defines sow, piglets, and sounder.", "sow is an adult female pig, piglets are young pigs, and a sounder is a group of pigs"),
                ("clue", "Uses the guiding action as evidence.", "sow guiding them away from the gate shows that the piglets are the young animals"),
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
                min_words=28,
            ),
            _two(
                "The pen sheltered a hen and three chicks. At dusk, the wider flock crossed the yard and settled near the coop.",
                "Distinguish pen, chicks, and flock using both place and relationship clues.",
                "The pen is the sheltered enclosure, the chicks are the young birds beside the hen, and the flock is the wider group crossing the yard.",
                ("place", "Identifies the enclosure.", "pen is the sheltered enclosure"),
                ("relations", "Distinguishes young birds from the larger group.", "chicks are the young birds beside the hen, and the flock is the wider group"),
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
                min_words=22,
            ),
        ],
        "transfer": [
            _two(
                "At the wildlife centre, a doe watched her fawn join a small herd moving toward the shaded water trough.",
                "Transfer the adult-young-group pattern to this sentence and use the watching clue.",
                "The doe is the adult female deer, the fawn is the young deer, and the herd is the group. The doe watching the fawn supports the adult-young relationship.",
                ("pattern", "Maps all three deer terms.", "doe is the adult female deer, the fawn is the young deer, and the herd is the group"),
                ("evidence", "Uses the watching action as support.", "doe watching the fawn supports the adult-young relationship"),
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
                min_words=25,
            ),
        ],
        "support": [
            _one(
                "A cow licked her calf while the cattle waited beside the trough.",
                "Name the adult, young one, and group.",
                "The cow is the adult, the calf is the young one, and cattle names the group.",
                "cow is the adult, the calf is the young one, and cattle names the group",
                description="Maps the three relationship terms.",
                skills=["vocab.chapter_word_usage"],
            ),
            _one(
                "A duck led her ducklings back toward the flock gathered by the pond.",
                "Use the action to distinguish ducklings from flock.",
                "Ducklings are the young birds being led, while flock refers to the larger group by the pond.",
                "Ducklings are the young birds being led, while flock refers to the larger group",
                description="Uses the leading clue to distinguish young and group.",
                skills=["reading.word_meaning_context"],
            ),
            _one(
                "The kennel housed one dog and her pups; later the pack returned from training.",
                "Explain kennel, pups, and pack.",
                "A kennel is the dogs' shelter, pups are young dogs, and a pack is a group of dogs.",
                "kennel is the dogs' shelter, pups are young dogs, and a pack is a group",
                description="Defines place, young, and group from context.",
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
            ),
            _one(
                "A female goat called her kid away from the herd near the rocky slope.",
                "Which word names the young goat and which names the group?",
                "Kid names the young goat, while herd names the group on the slope.",
                "Kid names the young goat, while herd names the group",
                description="Distinguishes the young-one and group words.",
                skills=["reading.word_meaning_context"],
            ),
            _two(
                "An adult goose guarded two goslings as the gaggle moved across the farm path.",
                "Build the relationship map and identify the action clue.",
                "The goose is the adult, goslings are the young, and gaggle names the group. Guarded is the clue connecting the adult with the young birds.",
                ("map", "Maps adult, young, and group.", "goose is the adult, goslings are the young, and gaggle names the group"),
                ("clue", "Uses the guarding action.", "Guarded is the clue connecting the adult with the young birds"),
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
            ),
        ],
    },
    "tank-conservation-paragraph": {
        "guided": [
            _two(
                "The canteen rinses vegetables under a running tap for ten minutes. A clean basin is available, and the collected rinse water can be used on non-edible border plants.",
                "Recommend one change and connect it to a water-saving benefit.",
                "The canteen should rinse the vegetables in the basin and reuse the collected water on border plants. This limits tap flow and gives the same clean water a second safe use.",
                ("action", "Recommends basin collection and reuse.", "rinse the vegetables in the basin and reuse the collected water on border plants"),
                ("benefit", "Explains the conservation benefit.", "limits tap flow and gives the same clean water a second safe use"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
                min_words=24,
            ),
            _two(
                "A rooftop tank overflows every evening because the float valve sticks. The caretaker can shut the inlet temporarily, but the faulty valve also needs replacement.",
                "Write a short response using because and but to separate immediate action from repair.",
                "The caretaker should close the inlet because the overflowing tank is wasting water, but the float valve must be replaced before normal filling resumes.",
                ("immediate", "States the immediate response and reason.", "close the inlet because the overflowing tank is wasting water"),
                ("repair", "Uses but to state the lasting repair.", "but the float valve must be replaced before normal filling resumes"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
            ),
        ],
        "independent": [
            _two(
                "During sports practice, half-filled cups are left beside the field. A labelled collection can is available for clean leftover water, and the grounds team waters young trees after practice.",
                "Write a focused action paragraph with a benefit and one hygiene limit.",
                "Players can pour untouched leftover water into the labelled can, and the grounds team can use it on the young trees. This avoids discarding clean water, but cups containing mud or food must not be added.",
                ("plan", "Explains collection and reuse.", "pour untouched leftover water into the labelled can, and the grounds team can use it on the young trees"),
                ("limit", "States the hygiene boundary.", "cups containing mud or food must not be added"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=30,
            ),
            _two(
                "The school garden is watered at noon with a wide spray. Much of the water lands on the path or evaporates before reaching the roots. Drip lines and an early-morning schedule are available.",
                "Propose a two-part improvement and justify it in a short paragraph.",
                "The garden team should use drip lines early in the morning so water reaches the roots with less evaporation. The change also prevents a wide spray from wasting water on the path.",
                ("improvement", "Combines drip lines with morning watering.", "use drip lines early in the morning so water reaches the roots"),
                ("reason", "Explains both avoided losses.", "less evaporation"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=27,
            ),
        ],
        "transfer": [
            _two(
                "A community hall leaves all lights and fans on during a two-hour lunch break. One switch panel controls each empty room, but a vaccine refrigerator must remain powered.",
                "Transfer the conservation structure to electricity: recommend an action and state the exception.",
                "The caretaker should switch off lights and fans in empty rooms because they are not being used, but the vaccine refrigerator must remain powered for safe storage.",
                ("action", "Recommends switching off unused equipment with a reason.", "switch off lights and fans in empty rooms because they are not being used"),
                ("exception", "Protects the essential refrigerator.", "but the vaccine refrigerator must remain powered for safe storage"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
                min_words=24,
            ),
        ],
        "support": [
            _two(
                "A washroom tap continues dripping after it is closed. A bucket can catch the drips until a plumber arrives.",
                "State the immediate action and the necessary final repair.",
                "The caretaker can catch the drips in a bucket for cleaning, but a plumber must repair the tap to stop the waste.",
                ("temporary", "States the useful temporary action.", "catch the drips in a bucket for cleaning"),
                ("repair", "States the lasting repair.", "plumber must repair the tap to stop the waste"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
            ),
            _two(
                "A hose floods the tree pit while the nearby soil stays dry. A watering can can direct a measured amount around the roots.",
                "Recommend the better tool and explain why.",
                "The gardener should use the watering can because it directs a measured amount around the roots and avoids flooding one spot.",
                ("choice", "Selects the watering can.", "use the watering can"),
                ("reason", "Explains measured root watering.", "directs a measured amount around the roots and avoids flooding one spot"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
            ),
            _two(
                "A drinking-water jug is emptied at closing time even though the water is still clean. The cleaner needs water for the entrance plants.",
                "Write a reuse action and a safety limit.",
                "The cleaner can use the untouched jug water on the entrance plants, but water that has been contaminated should not be reused this way.",
                ("reuse", "States the safe second use.", "use the untouched jug water on the entrance plants"),
                ("limit", "States the contamination boundary.", "contaminated should not be reused this way"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
            ),
            _two(
                "Rain fell overnight, but the automatic sprinkler is scheduled to run at dawn. The soil is already wet two centimetres below the surface.",
                "Use the evidence to decide whether watering should continue.",
                "The sprinkler should be paused because the soil is already wet below the surface. Watering now would waste stored water.",
                ("decision", "Pauses irrigation.", "sprinkler should be paused because the soil is already wet"),
                ("benefit", "Explains the avoided waste.", "Watering now would waste stored water"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
            ),
            _two(
                "A class wants to wash paint trays using a full running tap. Two basins can be used for a first rinse and a final rinse.",
                "Build a brief two-basin plan and state its benefit.",
                "The class can loosen paint in the first basin and finish in the second, using the tap only to fill them. This controls how much water is used.",
                ("plan", "Explains both basin stages.", "loosen paint in the first basin and finish in the second"),
                ("benefit", "States controlled water use.", "controls how much water is used"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
            ),
        ],
    },
    "tank-inquiry-procedure": {
        "guided": [
            _two(
                "Inspection card: the lid closes firmly; the outlet tap leaks; the inside is clean. Repair kit: new tap washer, brush, lid hinge. Only evidence on the card may guide work.",
                "Select the relevant repair and write the first two safe steps.",
                "Select the new tap washer because the outlet leaks. First close the water supply, then ask an authorised adult to replace the washer and test the tap.",
                ("selection", "Selects the washer from the evidence.", "Select the new tap washer because the outlet leaks"),
                ("steps", "Orders shutoff before authorised repair and testing.", "First close the water supply, then ask an authorised adult to replace the washer and test the tap"),
                skills=["research.information_selection", "writing.procedure"],
                min_words=24,
                ordered=True,
            ),
            _two(
                "Fact packet: Container A is food-grade and has a fitted lid. Container B once held floor cleaner. The task is to choose a vessel for emergency non-drinking handwashing after adult cleaning.",
                "Choose from the packet and state the rejection reason.",
                "Container A is the only candidate for adult cleaning and non-drinking use because it is food-grade with a lid. Container B must be rejected because it held floor cleaner.",
                ("choice", "Selects A within the stated limit.", "Container A is the only candidate for adult cleaning and non-drinking use"),
                ("rejection", "Rejects B using its history.", "Container B must be rejected because it held floor cleaner"),
                skills=["research.information_selection", "writing.procedure"],
            ),
        ],
        "independent": [
            _two(
                "Survey packet: Room 1 has a dripping tap. Room 2 has a loose handle. Room 3 has both faults. The maintenance form needs one row per room, all faults listed, and a completion check after repair.",
                "Write a procedure that prevents double-counting and records completion.",
                "Create one row for each room and list every fault in that row, including both faults for Room 3. Group the repair work by fault, then mark each room complete only after both its inspection and repair check pass.",
                ("record", "Keeps one row per room while listing both faults.", "one row for each room and list every fault in that row, including both faults for Room 3"),
                ("completion", "Defines the completion check.", "mark each room complete only after both its inspection and repair check pass"),
                skills=["research.information_selection", "writing.procedure"],
                interaction="paragraph_text",
                min_words=32,
                ordered=True,
            ),
            _two(
                "Water-quality card: collect a sample in a clean labelled bottle; do not touch the inside of the cap; keep it shaded; deliver it to the authorised lab the same day. Children may observe but not collect the sample alone.",
                "Turn the card into a safe numbered procedure and explain what a child may and may not do.",
                "An authorised adult labels a clean bottle, collects the sample without touching the cap's inside, keeps it shaded, and delivers it to the lab that day. A child may observe but must not collect the sample alone.",
                ("procedure", "Preserves collection, handling, shade, and delivery instructions.", "labels a clean bottle, collects the sample without touching the cap's inside, keeps it shaded, and delivers it to the lab that day"),
                ("boundary", "States the child safety limit.", "child may observe but must not collect the sample alone"),
                skills=["research.information_selection", "writing.procedure"],
                interaction="paragraph_text",
                min_words=32,
                ordered=True,
            ),
        ],
        "transfer": [
            _two(
                "Library repair packet: books with loose pages go to the binding tray; wet books are stood open on the drying rack; books with no damage return by call number. A return must not be shelved before inspection.",
                "Write the sorting procedure and its no-shelving boundary.",
                "Inspect every return first. Place loose-page books in the binding tray, stand wet books on the drying rack, and shelve only undamaged books by call number. No book should be shelved before inspection.",
                ("steps", "Uses all three evidence-based destinations.", "Place loose-page books in the binding tray, stand wet books on the drying rack, and shelve only undamaged books by call number"),
                ("boundary", "States inspection before shelving.", "No book should be shelved before inspection"),
                skills=["research.information_selection", "writing.procedure"],
                min_words=28,
                ordered=True,
            ),
        ],
        "support": [
            _two(
                "Card: place the covered barrel under the east gutter; check that the screen is clean; use the tap for the flower beds every Tuesday and Friday.",
                "Select only the location and first two actions from the card.",
                "Place the covered barrel under the east gutter. Then check the clean screen before using the tap for the flower beds on Tuesday and Friday.",
                ("location", "Uses the supplied gutter location.", "under the east gutter"),
                ("actions", "Orders screen check before scheduled use.", "check the clean screen before using the tap"),
                skills=["research.information_selection", "writing.procedure"],
                ordered=True,
            ),
            _two(
                "Fault card: the inlet screen is torn; the overflow pipe is clear; the cover closes properly. Available actions are replace screen, clear pipe, replace cover.",
                "Choose the needed action and reject the two unsupported repairs.",
                "Replace the torn inlet screen. Do not clear the pipe or replace the cover because both are already working properly.",
                ("repair", "Selects screen replacement.", "Replace the torn inlet screen"),
                ("reject", "Rejects both unsupported actions.", "Do not clear the pipe or replace the cover because both are already working properly"),
                skills=["research.information_selection", "writing.procedure"],
            ),
            _two(
                "Comparison card: a covered steel drum limits falling dirt; an unglazed clay pot can cool a small amount through evaporation; neither card claims to remove salt.",
                "State the two supported uses and the unsupported claim.",
                "The covered steel drum limits falling dirt, and the clay pot can cool a small amount through evaporation. Neither item is shown to remove dissolved salt.",
                ("facts", "States both supported uses.", "covered steel drum limits falling dirt, and the clay pot can cool a small amount through evaporation"),
                ("limit", "Rejects salt-removal invention.", "Neither item is shown to remove dissolved salt"),
                skills=["research.information_selection"],
            ),
            _two(
                "Checklist: label each tap once; mark drip, loose handle, or both; group repairs; verify the tap after work. Tap C has both faults.",
                "Explain how to record Tap C and how to finish its row.",
                "Record Tap C once and mark both the drip and loose handle in that row. Complete the row only after both repairs have been verified.",
                ("record", "Avoids double-counting while listing both faults.", "Record Tap C once and mark both the drip and loose handle"),
                ("finish", "Requires verification of both repairs.", "only after both repairs have been verified"),
                skills=["research.information_selection", "writing.procedure"],
                ordered=True,
            ),
            _two(
                "Safety note: an unlabelled drum has an unknown history. Children must not open or clean it. An authorised adult decides whether it is rejected or assigned a safe non-drinking use.",
                "Write the prohibition and the adult decision step.",
                "Children must not open or clean the unlabelled drum. An authorised adult must inspect its history and either reject it or approve a safe non-drinking use.",
                ("prohibition", "States what children must not do.", "Children must not open or clean the unlabelled drum"),
                ("decision", "Reserves inspection and decision for an adult.", "authorised adult must inspect its history and either reject it or approve a safe non-drinking use"),
                skills=["research.information_selection", "writing.procedure"],
            ),
        ],
    },
}


_LAUNCH_VARIANTS = {
    "tank-purpose-sequence": {
        "transfer": [
            _two(
                "At a weekend camp, volunteers inspect sealed water cans, carry approved cans to a raised stand, attach a clean tap, and place empty cans on a return cart.",
                "Explain the route in order and state the organising purpose.",
                "Volunteers inspect each seal, move approved cans to the stand, attach the tap, and return empty cans on the cart. This sequence keeps drinking water safe and the used containers organised.",
                ("route", "Orders inspection, setup, and return.", "inspect each seal, move approved cans to the stand, attach the tap, and return empty cans on the cart"),
                ("purpose", "States the central safety and organisation purpose.", "keeps drinking water safe and the used containers organised"),
                skills=["reading.event_sequence", "reading.paragraph_main_idea"],
                min_words=27,
                ordered=True,
            ),
        ],
        "review": [
            _two(
                "Before cleaning a class aquarium, the science club switches off the pump, moves the fish to a prepared tub, drains and wipes the tank, refills it, and returns the fish.",
                "Summarise the sequence and its main purpose.",
                "The club switches off the pump, moves the fish, cleans and refills the tank, and then returns the fish. The ordered steps protect the fish while the aquarium is cleaned.",
                ("sequence", "Preserves the safe cleaning order.", "switches off the pump, moves the fish, cleans and refills the tank, and then returns the fish"),
                ("purpose", "States why the order matters.", "protect the fish while the aquarium is cleaned"),
                skills=["reading.event_sequence", "reading.paragraph_main_idea"],
                min_words=25,
                ordered=True,
            ),
            _two(
                "After a storm, relief workers check packet dates, sort undamaged water packets into crates, carry the crates to marked counters, and record each distributed crate.",
                "Retell the process and identify its central purpose.",
                "Workers check dates, sort safe packets, move the crates to marked counters, and record distribution. The process provides usable water in an orderly, traceable way.",
                ("process", "Orders checking, sorting, moving, and recording.", "check dates, sort safe packets, move the crates to marked counters, and record distribution"),
                ("idea", "States the distribution purpose.", "provides usable water in an orderly, traceable way"),
                skills=["reading.event_sequence", "reading.paragraph_main_idea"],
                min_words=22,
                ordered=True,
            ),
        ],
    },
    "tank-design-inference": {
        "transfer": [
            _two(
                "A bird bath has a wide shallow edge and three rough stones rising above the water. Sparrows land on the edge, and a wet beetle climbs onto a stone.",
                "Infer one practical job of each feature and support both inferences with the scene.",
                "The shallow edge gives small birds a steady place to land and drink. The raised rough stones give a wet insect a grip and a route out of the water.",
                ("edge", "Infers the job of the shallow edge.", "shallow edge gives small birds a steady place to land and drink"),
                ("stones", "Infers the job of the rough stones.", "rough stones give a wet insect a grip and a route out of the water"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=27,
            ),
        ],
        "review": [
            _two(
                "A drinking-water unit stands on a low platform. Its taps face the corridor, and a removable tray below them catches drops after children fill bottles.",
                "What does the design suggest about the platform and tray? Give evidence for both ideas.",
                "The platform raises the taps so children can reach and use them from the corridor. The removable tray catches spills and can be emptied for easier cleaning.",
                ("platform", "Infers the platform's practical job.", "platform raises the taps so children can reach and use them from the corridor"),
                ("tray", "Infers the tray's practical job.", "removable tray catches spills and can be emptied for easier cleaning"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=25,
            ),
            _two(
                "A garden tank has numbered level marks beside a clear strip and bright leaf patterns around its lid. The gardener checks the marks before opening the hose, while visitors admire the painted leaves.",
                "Separate the practical feature from the decorative feature and explain your reasoning.",
                "The numbered clear strip is practical because it shows how much water remains before watering. The leaf pattern is decorative because it adds a garden identity without measuring the water.",
                ("practical", "Identifies and explains the measuring feature.", "numbered clear strip is practical because it shows how much water remains"),
                ("decorative", "Identifies and explains the identity feature.", "leaf pattern is decorative because it adds a garden identity without measuring the water"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=28,
            ),
        ],
    },
    "tank-contractions": {
        "transfer": [
            _two(
                "A notice beside the garden drum says, 'They'll refill it when it's empty.'",
                "Expand both contractions and write the complete sentence without changing the order or meaning.",
                "They will refill it when it is empty.",
                ("expansion", "Expands both contractions accurately.", "They will", "it is"),
                ("sentence", "Produces the complete sentence in the original order.", "They will refill it when it is empty"),
                skills=["grammar.sentence_order", "writing.complete_sentence"],
                min_words=8,
                ordered=True,
            ),
        ],
        "review": [
            _two(
                "The monitor explains, 'We haven't closed the valve because it's still filling.'",
                "Rewrite the message with both contractions expanded as one complete sentence.",
                "We have not closed the valve because it is still filling.",
                ("forms", "Expands haven't and it's correctly.", "We have not", "it is"),
                ("complete", "Keeps the reason in a complete sentence.", "We have not closed the valve because it is still filling"),
                skills=["grammar.sentence_order", "writing.complete_sentence"],
                min_words=10,
                ordered=True,
            ),
            _two(
                "The log reads, 'Ravi'd checked the lid, so he didn't reopen it.'",
                "Expand the two shortened forms while preserving the completed action and sentence order.",
                "Ravi had checked the lid, so he did not reopen it.",
                ("expansion", "Expands the completed-action and negative forms.", "Ravi had checked", "he did not reopen"),
                ("order", "Preserves the cause followed by the result.", "Ravi had checked the lid, so he did not reopen it"),
                skills=["grammar.sentence_order", "writing.complete_sentence"],
                min_words=11,
                ordered=True,
            ),
        ],
    },
    "tank-exclamation-emotion": {
        "transfer": [
            _two(
                "After waiting for the rain barrel to fill, Meera smiles and says, 'oh the tank is full at last'",
                "Rewrite her words with correct capitals and punctuation, then name the feeling shown by the situation.",
                "Oh, the tank is full at last! Meera sounds relieved and delighted because the long wait has ended.",
                ("sentence", "Uses a capital, comma, and exclamation mark.", "Oh, the tank is full at last!"),
                ("feeling", "Names and explains the feeling from context.", "relieved and delighted because the long wait has ended"),
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=18,
            ),
        ],
        "review": [
            _two(
                "A pipe splits and water sprays across the path. The caretaker shouts, 'look the pipe has burst'",
                "Punctuate the warning and explain the emotion carried by the words and action.",
                "Look, the pipe has burst! The shout shows alarm because the sudden leak needs immediate attention.",
                ("sentence", "Capitalizes and punctuates the warning.", "Look, the pipe has burst!"),
                ("emotion", "Infers alarm from the urgent scene.", "shows alarm because the sudden leak needs immediate attention"),
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=16,
            ),
            _two(
                "When the first drops reach a dry seed bed, Kabir claps and calls, 'what welcome rain this is'",
                "Rewrite the exclamation correctly and state why Kabir reacts that way.",
                "What welcome rain this is! Kabir feels joyful because the dry seed bed is finally receiving water.",
                ("sentence", "Uses correct capitalization and end punctuation.", "What welcome rain this is!"),
                ("reason", "Connects the joy to the dry garden receiving rain.", "feels joyful because the dry seed bed is finally receiving water"),
                skills=["grammar.punctuation_capitalization", "reading.sentence_comprehension"],
                min_words=17,
            ),
        ],
    },
    "tank-animal-word-meaning": {
        "transfer": [
            _two(
                "A mare nudged her foal toward the herd when thunder sounded beyond the field.",
                "Identify the adult, young animal, and group, then use the action clue to explain their relationship.",
                "The mare is the adult horse, the foal is her young, and the herd is the group. Her nudge guides the young horse toward safety with the others.",
                ("words", "Maps the adult, young, and group words.", "mare is the adult horse, the foal is her young, and the herd is the group"),
                ("clue", "Uses the action to explain the relationship.", "nudge guides the young horse toward safety with the others"),
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
                min_words=27,
            ),
        ],
        "review": [
            _two(
                "A hen scratched the soil while her chicks followed, and the flock gathered near the grain tray.",
                "Explain the meanings of hen, chicks, and flock using the action in the sentence.",
                "Hen names the adult bird, chicks names her young, and flock names the group. The chicks following the hen confirms the family relationship.",
                ("map", "Distinguishes adult, young, and group.", "Hen names the adult bird, chicks names her young, and flock names the group"),
                ("context", "Uses following as the relationship clue.", "chicks following the hen confirms the family relationship"),
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
                min_words=23,
            ),
            _two(
                "A doe paused beside her fawn as the herd crossed a shallow stream ahead of them.",
                "Build the adult-young-group map and explain the protective clue.",
                "The doe is the adult deer, the fawn is the young deer, and the herd is the group. The doe pausing beside the fawn suggests that she is watching over it.",
                ("map", "Identifies all three animal relationships.", "doe is the adult deer, the fawn is the young deer, and the herd is the group"),
                ("clue", "Explains the protective action.", "doe pausing beside the fawn suggests that she is watching over it"),
                skills=["vocab.chapter_word_usage", "reading.word_meaning_context"],
                min_words=29,
            ),
        ],
    },
    "tank-conservation-paragraph": {
        "transfer": [
            _two(
                "During art class, a tap runs while brushes are scrubbed one at a time. A jar can hold clean rinse water, but paint water must still go into the labelled disposal sink.",
                "Write a short recommendation using because and but, with both the saving action and the safety limit.",
                "Students should turn off the tap and rinse brushes in the jar because this reduces continuous water flow. They can reuse clean rinse water, but paint water must go into the labelled disposal sink.",
                ("action", "Recommends a feasible water-saving action with because.", "rinse brushes in the jar because this reduces continuous water flow"),
                ("limit", "Uses but to preserve the disposal boundary.", "but paint water must go into the labelled disposal sink"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=30,
            ),
        ],
        "review": [
            _two(
                "A courtyard tap drips all night. A bucket can catch the drops for cleaning, but the loose washer will keep causing waste until it is repaired.",
                "Write two connected sentences that give an immediate action and a lasting solution.",
                "Place a bucket below the tap because the collected drops can be used for cleaning. This prevents some waste, but the loose washer must be repaired to stop the leak.",
                ("immediate", "Uses because to justify collection and reuse.", "bucket below the tap because the collected drops can be used for cleaning"),
                ("lasting", "Uses but to state the necessary repair.", "but the loose washer must be repaired to stop the leak"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=27,
            ),
            _two(
                "The garden sprinkler is scheduled after a night of steady rain. Most soil is damp, but two covered pots near the wall may still be dry.",
                "Recommend a water-wise response in a short paragraph using because and but.",
                "Cancel the full sprinkler cycle because the rain has already watered most of the garden. Check the covered pots by hand, but water only those that are still dry.",
                ("decision", "Uses because to justify cancelling the full cycle.", "Cancel the full sprinkler cycle because the rain has already watered most of the garden"),
                ("exception", "Uses but to state the limited follow-up.", "but water only those that are still dry"),
                skills=["grammar.connectors_because_and_but", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=27,
            ),
        ],
    },
    "tank-inquiry-procedure": {
        "transfer": [
            _two(
                "Inspection cards say Filter A has an intact lid and clear outlet, while Filter B has a cracked lid and loose outlet. Only intact units may be prepared for the class stall.",
                "Select the usable unit and write the safe preparation steps supported by the cards.",
                "Select Filter A because its lid and outlet are intact. Wash hands, ask an adult to rinse the approved unit, fit the lid, check the outlet, and label it ready; keep Filter B out of use.",
                ("selection", "Selects only the unit supported by the inspection facts.", "Select Filter A because its lid and outlet are intact"),
                ("procedure", "Orders preparation and rejects the damaged unit.", "Wash hands, ask an adult to rinse the approved unit, fit the lid, check the outlet, and label it ready; keep Filter B out of use"),
                skills=["research.information_selection", "writing.procedure"],
                interaction="paragraph_text",
                min_words=31,
                ordered=True,
            ),
        ],
        "review": [
            _two(
                "A checklist records: the bottle-filling tap is clean, its drain cover is missing, and a spare cover is stored with the caretaker. The station must stay closed until every safety item is complete.",
                "Use only the checklist facts to write the inspection and reopening procedure.",
                "Record that the clean tap cannot reopen because the drain cover is missing. Keep the station closed, ask the caretaker to fit the spare cover, inspect the fit, and then record that reopening is allowed.",
                ("facts", "Selects the clean tap, missing cover, and spare cover facts.", "clean tap cannot reopen because the drain cover is missing"),
                ("steps", "Orders closure, fitting, inspection, and reopening.", "Keep the station closed, ask the caretaker to fit the spare cover, inspect the fit, and then record that reopening is allowed"),
                skills=["research.information_selection", "writing.procedure"],
                interaction="paragraph_text",
                min_words=31,
                ordered=True,
            ),
            _two(
                "A rain study provides two identical jars, a ruler, labels, and a table. The plan says to place one jar in the open and one under a roof edge, measure both at the same time, and never taste collected water.",
                "Write the procedure using every supplied control and the stated safety boundary.",
                "Label the identical jars, place one in the open and one under the roof edge, and measure both with the ruler at the same time. Record both results in the table, and never taste the collected water.",
                ("controls", "Uses identical jars, different positions, and one measurement time.", "place one in the open and one under the roof edge, and measure both with the ruler at the same time"),
                ("boundary", "Records results and preserves the safety rule.", "Record both results in the table, and never taste the collected water"),
                skills=["research.information_selection", "writing.procedure"],
                interaction="paragraph_text",
                min_words=34,
                ordered=True,
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
    MANIFEST["chapter"]["content_version"] = "2026-07-15.2"
    MANIFEST["chapter"]["certification_version"] = "2026-07-15.2"
    anchors = {
        anchor["anchor_id"]: anchor for anchor in MANIFEST["source_anchors"]
    }
    anchors["eng_c5_ch06:inquiry:12-14"]["coverage_treatment"] = (
        "zidd_equivalent"
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
            level[target_key].extend(
                _open_activity(
                    level_id=level_id,
                    phase=phase_name,
                    index=start + offset,
                    principle=principle,
                    level_skills=level["skill_ids"],
                    task=task,
                )
                for offset, task in enumerate(additions[phase_name])
            )
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
    "tank-conservation-paragraph-guided-1": {
        "recommendation": "water the roots with a can early in the morning",
        "reason": "less water will evaporate or land on the path",
    },
    "tank-conservation-paragraph-independent-1": {
        "benefit": "reuses water that would be discarded",
    },
    "tank-conservation-paragraph-transfer-1": {
        "evidence": "water continues to enter after the flush",
        "response": "close the supply valve to stop further waste",
    },
    "tank-conservation-paragraph-review-1": {
        "benefit": "avoids using stored water when nature has supplied enough",
    },
    "tank-inquiry-procedure-guided-1": {
        "selection": "secure lid and clear overflow do not need repair now",
    },
    "tank-inquiry-procedure-guided-2": {
        "facts": "covered steel drum is suitable for protected storage",
    },
    "tank-inquiry-procedure-independent-1": {
        "selection": "classroom with both problems must not be counted as two separate rooms",
        "result": "group repairs by fault and record completion",
    },
    "tank-inquiry-procedure-independent-2": {
        "prohibition": "Do not ask children to clean or use the drum",
    },
    "tank-inquiry-procedure-transfer-1": {
        "evidence": "beds are still damp after recent rain",
        "decision": "watering should be delayed",
    },
    "tank-inquiry-procedure-transfer-2": {
        "rejection": "Container B should be rejected because its history is unknown and it smells of chemicals",
    },
    "eng_c5_ch06-assessment-tank-conservation-paragraph-1": {
        "reason": "reduces unnecessary electricity use",
    },
    "eng_c5_ch06-assessment-tank-conservation-paragraph-3": {
        "benefit": "reduce demand for new paper",
    },
    "eng_c5_ch06-assessment-tank-conservation-paragraph-4": {
        "reason": "idling wastes fuel and adds pollution",
    },
    "eng_c5_ch06-assessment-tank-inquiry-procedure-1": {
        "steps": "sort returned books by date, then flag any damaged covers for repair, and finally shelve sound books by call number",
    },
    "eng_c5_ch06-assessment-tank-inquiry-procedure-2": {
        "controls": "give equal amounts of water, and record growth at the same time each day",
    },
    "eng_c5_ch06-assessment-tank-inquiry-procedure-4": {
        "materials": "one cup of lentils. Add three cups of water",
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


_ATOMIC_REQUIREMENT_REPAIRS = {
    "tank-inquiry-procedure-independent-1": [
        (
            "steps",
            "Orders verification and repair tracking.",
            "First list each classroom once, then verify whether it has a drip, a loose handle, or both",
        ),
        (
            "result",
            "States the intended accurate outcome.",
            "Next group repairs by fault and record completion",
        ),
        (
            "selection",
            "Uses the overlap fact correctly.",
            "classroom with both problems must not be counted as two separate rooms",
        ),
    ],
    "tank-purpose-sequence-transfer-2": [
        (
            "main_idea",
            "States the main idea about fair use of stored water.",
            "The community is rationing stored water fairly",
        ),
        (
            "supporting_detail",
            "Names the schedule and register evidence that supports the main idea.",
            "fixed opening times and a bucket register support that idea",
        ),
    ],
    "tank-design-inference:guided:3": [
        (
            "practical_feature",
            "Explains the practical job of the broad base.",
            "The broad base catches splashes",
        ),
        (
            "identity_feature",
            "Explains what the painted lotus communicates.",
            "the painted lotus identifies the neighbourhood garden group",
        ),
    ],
    "tank-design-inference:bridge:1": [
        (
            "practical_feature",
            "Names the part that prevents the carrier from opening.",
            "The locking clip prevents the carrier from opening",
        ),
        (
            "identity_feature",
            "Names the mark that identifies the owner.",
            "the initials identify its owner",
        ),
    ],
    "tank-purpose-sequence:guided:3": [
        ("first", "Names the first water movement.", "The rain enters the gutter"),
        ("next", "Names the next water movement.", "passes through the leaf screen"),
        ("last", "Names the final water movement.", "finally collects in the blue garden drum"),
    ],
    "tank-purpose-sequence:bridge:1": [
        ("first", "Names where the water goes first.", "First the water leaves the hand pump"),
        ("next", "Names where the water goes next.", "next it fills the pail"),
        ("last", "Names where the water goes last.", "last it enters the covered pot"),
    ],
    "tank-design-inference-guided-1": [
        ("function", "Explains the barrel's practical function.", "The barrel still stores water safely"),
        ("identity", "Explains what the wheel pattern represents.", "the wheel pattern represents the repairer's occupation"),
    ],
    "tank-design-inference:guided:4": [
        ("function", "Explains the lid's practical purpose.", "The lid protects the grain from insects"),
        ("identity", "Explains the wave pattern's identity purpose.", "the wave pattern only shows the cooperative's identity"),
    ],
    "tank-design-inference-independent-1": [
        ("identity", "Explains what the fish sign represents.", "The fish sign represents the family's trade"),
        ("function", "Explains the chamber's practical job.", "the underground chamber helps keep stored water cool"),
    ],
    "tank-design-inference-review-1": [
        ("decision", "Selects the better tank for safe storage.", "The tank with the lid, clean inlet, and overflow is safer"),
        ("reason", "Explains how those features improve safety.", "those features manage contamination and excess water"),
    ],
    "tank-design-inference:revision_level_1:1": [
        ("function", "Explains the holes' practical role.", "The holes drain extra water"),
        ("identity", "Explains the drawing's identity role.", "the sunflower drawing labels the gardening team"),
    ],
    "tank-contractions-independent-2": [
        ("first_contraction", "Contracts I would accurately.", "I'd check the overflow"),
        ("second_contraction", "Contracts I am accurately.", "I'm not at school today"),
    ],
    "tank-contractions-review-1": [
        ("first_contraction", "Uses should not as shouldn't.", "You shouldn't touch the inlet"),
        ("second_contraction", "Uses is not as isn't.", "it isn't clean"),
    ],
    "tank-exclamation-emotion-independent-1": [
        ("punctuation", "Explains the feeling intensified by the punctuation.", "The punctuation intensifies worry"),
        ("context", "Uses the overnight drip as the reason for that feeling.", "the overnight drip has wasted water"),
    ],
    "tank-exclamation-emotion-independent-2": [
        (
            "emotion",
            "Names the joy expressed by the speaker.",
            "The speaker expresses joy",
        ),
        (
            "cause",
            "Connects the joy to the repaired channel collecting rainwater.",
            "the repaired channel successfully collected rainwater",
        ),
    ],
    "tank-animal-word-meaning:guided:3": [
        (
            "adult",
            "Identifies the mare as the adult horse.",
            "A mare is an adult female horse",
        ),
        (
            "young",
            "Identifies the foal as the young horse.",
            "a foal is a young horse",
        ),
        (
            "group",
            "Identifies the herd as the moving group.",
            "a herd is the larger group moving together",
        ),
    ],
    "tank-animal-word-meaning:guided:4": [
        ("adult", "Identifies the ewe as the adult sheep.", "The ewe is the adult female sheep"),
        ("young", "Identifies the lamb as the young sheep.", "the lamb is her young"),
        ("group", "Identifies the flock as the group.", "the flock is the group of sheep"),
    ],
    "tank-animal-word-meaning-review-1": [
        ("thanked", "Uses thanked to express gratitude.", "I thanked"),
        ("caretaker", "Uses caretaker for the person responsible for the tank.", "the caretaker for cleaning the water tank"),
    ],
    "tank-animal-word-meaning:bridge:1": [
        ("adult", "Identifies the adult animal.", "The cow is the adult"),
        ("young", "Identifies the young animal.", "the calf is the young one"),
        ("group", "Identifies the group term.", "cattle names the group"),
    ],
    "tank-animal-word-meaning:revision_level_1:1": [
        ("shelter", "Defines kennel as the shelter.", "A kennel is the dogs' shelter"),
        ("young", "Defines pups as young dogs.", "pups are young dogs"),
        ("group", "Defines pack as a group of dogs.", "a pack is a group of dogs"),
    ],
    "tank-animal-word-meaning:revision_level_2:1": [
        ("young", "Identifies the young-goat word.", "Kid names the young goat"),
        ("group", "Identifies the group word.", "herd names the group on the slope"),
    ],
    "eng_c5_ch06-assessment-tank-design-inference-3": [
        ("information", "Explains which feature gives route information.", "The mural gives route information"),
        ("weather", "Explains which feature manages rain.", "the angled roof directs rain away from passengers"),
    ],
    "eng_c5_ch06-assessment-tank-contractions-4": [
        ("first_contraction", "Uses would not as wouldn't.", "Priya wouldn't enter the lab"),
        ("second_contraction", "Uses could not as couldn't.", "she couldn't find her goggles"),
    ],
    "eng_c5_ch06-assessment-tank-contractions-5": [
        (
            "rule",
            "States what an apostrophe replaces in a contraction.",
            "A contraction uses an apostrophe for omitted letters without changing meaning",
        ),
        (
            "example",
            "Contracts 'we are ready' accurately.",
            "'we are ready' becomes 'we're ready'",
        ),
    ],
    "eng_c5_ch06-assessment-tank-exclamation-emotion-3": [
        ("emotion", "Names the speaker's emotion.", "The speaker shows wonder"),
        ("cause", "Explains the event that causes the emotion.", "a delicate seedling managed to emerge through hard soil"),
    ],
    "eng_c5_ch06-assessment-tank-animal-word-meaning-4": [
        (
            "adult",
            "Identifies the doe as the adult female.",
            "The doe is the adult female",
        ),
        (
            "young",
            "Identifies the fawn as the young deer.",
            "the fawn is the young deer",
        ),
        (
            "group",
            "Identifies the herd as the group.",
            "the herd is the group",
        ),
    ],
}


_SELECTED_OPTION_REPAIRS = {
    "tank-contractions-co": {
        "prompt": (
            "Which option rewrites both ideas with standard contractions while "
            "keeping the meaning?"
        ),
    },
    "tank-exclamation-emotion-guided-2": {
        "prompt": (
            "Which option names the feeling created by the phrase 'clever way'?"
        ),
    },
    "tank-conservation-paragraph-co": {
        "prompt": (
            "Which option gives the problem, an immediate action with its reason, "
            "and the permanent fix?"
        ),
        "accepted_answer": (
            "The tap drips between classes, so catch and reuse the clean water "
            "because it can wash brushes, then repair the washer to stop the leak."
        ),
    },
    "tank-inquiry-procedure-co": {
        "prompt": (
            "Which option uses the supplied facts to give a safe collection plan "
            "and its purpose?"
        ),
        "accepted_answer": (
            "Collect from the west roof in a clean, lidded barrel, then use the tap "
            "to water the nursery twice a week."
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
    for activity_id, repair in _SELECTED_OPTION_REPAIRS.items():
        activity = activities[activity_id]
        activity["prompt"] = repair["prompt"]
        accepted_answer = repair.get("accepted_answer")
        if accepted_answer is not None:
            old_answer = activity["accepted_answers"][0]
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


_ASSESSMENT_SELECTED_OPTION_REFINEMENTS = {
    "eng_c5_ch06-assessment-tank-purpose-sequence-5": {
        "prompt": "Which option states the main idea most accurately?",
        "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea",
        ],
        "options": [
            "A tank makes new water whenever its lid is closed.",
            (
                "A covered tank protects collected water and keeps it available "
                "for later use."
            ),
            "A tank is useful only while rain is falling into it.",
            "Covering a tank removes the water already stored inside.",
        ],
        "accepted_answer": (
            "A covered tank protects collected water and keeps it available for "
            "later use."
        ),
    },
    "eng_c5_ch06-assessment-tank-purpose-sequence-4": {
        "prompt": "Which summary preserves the process and its final purpose?",
        "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea",
        ],
        "options": [
            (
                "Kitchen scraps and dry leaves are mixed and turned until they "
                "become compost for the soil."
            ),
            (
                "Dark compost is placed in an empty bin before vegetable peels "
                "and dry leaves are removed."
            ),
            (
                "Vegetable peels are kept separate from dry leaves so that the "
                "mixture never changes."
            ),
            "The bin is turned weekly only to make the dark compost lighter.",
        ],
        "accepted_answer": (
            "Kitchen scraps and dry leaves are mixed and turned until they "
            "become compost for the soil."
        ),
    },
    "eng_c5_ch06-assessment-tank-exclamation-emotion-4": {
        "prompt": "Which interpretation of 'Oh!' fits the surrounding event?",
        "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension",
        ],
        "options": [
            (
                "It signals sudden realisation and concern about the forgotten "
                "library book."
            ),
            "It shows delight because the book was returned safely.",
            "It is a greeting to another passenger on the bus.",
            "It shows anger because the library refused to lend the book.",
        ],
        "accepted_answer": (
            "It signals sudden realisation and concern about the forgotten "
            "library book."
        ),
    },
    "eng_c5_ch06-assessment-tank-contractions-1": {
        "prompt": (
            "Which option uses both contractions correctly without changing the "
            "meaning?"
        ),
        "skill_ids": ["grammar.sentence_order"],
        "options": [
            "Asha couldn't attend practice because she hadn't completed her project.",
            "Asha can't attend practice because she hasn't complete her project.",
            "Asha can't attend practice because she hasn't completed her project.",
            "Asha can attend practice because she hasn't completed her project.",
        ],
        "accepted_answer": (
            "Asha can't attend practice because she hasn't completed her project."
        ),
    },
    "eng_c5_ch06-assessment-tank-contractions-2": {
        "prompt": (
            "Which option contracts both verb groups without changing their "
            "tense or meaning?"
        ),
        "skill_ids": ["grammar.sentence_order"],
        "options": [
            "The museum wouldn't open until the guide wasn't busy.",
            "The museum won't open until the guide isn't busy.",
            "The museum won't open until the guide is busy.",
            "The museum will open until the guide isn't busy.",
        ],
        "accepted_answer": "The museum won't open until the guide isn't busy.",
    },
    "eng_c5_ch06-assessment-tank-contractions-3": {
        "prompt": (
            "Which option keeps the same present-perfect meaning and uses both "
            "contractions correctly?"
        ),
        "skill_ids": ["grammar.sentence_order"],
        "options": [
            "We hadn't packed lunch because the bus hadn't arrived.",
            "We haven't pack lunch because the bus hasn't arrive.",
            "We have packed lunch because the bus hasn't arrived.",
            "We haven't packed lunch because the bus hasn't arrived.",
        ],
        "accepted_answer": (
            "We haven't packed lunch because the bus hasn't arrived."
        ),
    },
    "eng_c5_ch06-assessment-tank-exclamation-emotion-5": {
        "prompt": "Which rule best explains how to interpret an exclamation?",
        "skill_ids": [
            "grammar.punctuation_capitalization",
            "reading.sentence_comprehension",
        ],
        "options": [
            (
                "Use the surrounding event and words to identify the feeling; "
                "the exclamation mark alone is not enough."
            ),
            "Treat every exclamation mark as a sign of joy.",
            "Ignore the surrounding event and look only at the punctuation.",
            "Use the first capitalised word as the name of the feeling.",
        ],
        "accepted_answer": (
            "Use the surrounding event and words to identify the feeling; the "
            "exclamation mark alone is not enough."
        ),
    },
    "eng_c5_ch06-assessment-tank-animal-word-meaning-3": {
        "prompt": "Which meaning of 'seal' fits the workers' action?",
        "skill_ids": [
            "vocab.chapter_word_usage",
            "reading.word_meaning_context",
        ],
        "options": [
            "a sea animal resting beside the tank",
            "to paint an animal sign on the wall",
            "to close the tank wall tightly so water cannot leak",
            "to remove part of the wall so water can escape",
        ],
        "accepted_answer": (
            "to close the tank wall tightly so water cannot leak"
        ),
    },
    "eng_c5_ch06-assessment-tank-inquiry-procedure-3": {
        "prompt": (
            "Which trip plan selects every relevant fact from the travel card "
            "without adding unsupported details?"
        ),
        "skill_ids": ["research.information_selection"],
        "options": [
            (
                "Take Bus 14 at 8:10, get off at school, and return at 3:10; "
                "no identity card is needed."
            ),
            (
                "Carry water and an identity card, board Bus 14 for its 8:10 "
                "departure, get off at the museum gate, and return with the "
                "group at 1:30."
            ),
            (
                "Bring lunch and a ticket, take Bus 41 at 8:30, and return from "
                "the market at 1:30."
            ),
            (
                "Carry only water, walk to the museum, and return whenever the "
                "visit ends."
            ),
        ],
        "accepted_answer": (
            "Carry water and an identity card, board Bus 14 for its 8:10 "
            "departure, get off at the museum gate, and return with the group "
            "at 1:30."
        ),
    },
    "eng_c5_ch06-assessment-tank-inquiry-procedure-4": {
        "prompt": (
            "Which procedure preserves both the quantities and the sequence on "
            "the recipe card?"
        ),
        "skill_ids": ["research.information_selection"],
        "options": [
            (
                "Rinse three cups of lentils, add one cup of water, then simmer "
                "and add salt."
            ),
            (
                "Add salt to one cup of lentils, rinse them, add three cups of "
                "water, and then simmer."
            ),
            "Rinse the lentils, add some water, and add salt whenever you like.",
            (
                "Rinse one cup of lentils, add three cups of water, simmer until "
                "soft, and add salt after cooking."
            ),
        ],
        "accepted_answer": (
            "Rinse one cup of lentils, add three cups of water, simmer until "
            "soft, and add salt after cooking."
        ),
    },
}

_OPEN_RESPONSE_ONLY_FIELDS = (
    "interaction_type",
    "rubric_criteria",
    "concept_slots",
    "forbidden_phrases",
    "min_response_words",
    "ordered_concept_slot_ids",
    "relevance_terms",
    "model_answer",
    "pass_score",
    "preflight_rule",
)


def _apply_assessment_mix() -> None:
    MANIFEST["chapter"]["content_version"] = "2026-07-16.2"
    MANIFEST["chapter"]["certification_version"] = "2026-07-16.2"
    items = {
        activity["activity_id"]: activity
        for activity in MANIFEST["chapter_assessment"]["items"]
    }
    missing = set(_ASSESSMENT_SELECTED_OPTION_REFINEMENTS) - set(items)
    if missing:
        raise ValueError(
            "missing_chapter_six_assessment_mix_items:" + ",".join(sorted(missing))
        )

    for activity_id, refinement in _ASSESSMENT_SELECTED_OPTION_REFINEMENTS.items():
        activity = items[activity_id]
        activity["kind"] = "selected_option"
        activity["prompt"] = refinement["prompt"]
        activity["skill_ids"] = list(refinement["skill_ids"])
        activity["options"] = list(refinement["options"])
        activity["accepted_answers"] = [refinement["accepted_answer"]]
        activity["teaching_block"] = (
            f"Use the new card to {_assessment_focus(activity)}. Compare every "
            "option with the visible details before choosing."
        )
        for field in _OPEN_RESPONSE_ONLY_FIELDS:
            activity.pop(field, None)

    for strand in MANIFEST["chapter_assessment"]["strands"]:
        strand_skills = set(strand["skill_ids"])
        strand_items = [
            activity
            for activity in items.values()
            if set(activity["skill_ids"]).issubset(strand_skills)
        ]
        actual_forms = {
            (
                "selected_option"
                if activity["kind"] == "selected_option"
                else "constructed_response"
            )
            for activity in strand_items
        }
        strand["evidence_forms"] = [
            form
            for form in ("selected_option", "constructed_response")
            if form in actual_forms
        ]


_apply_depth()
_apply_launch_variants()
_repair_open_authority()
_apply_semantic_quality()
_apply_assessment_mix()
