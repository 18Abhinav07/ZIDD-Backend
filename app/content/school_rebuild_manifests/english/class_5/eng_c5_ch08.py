"""Authored deep manifest for Class 5 English Chapter 8.

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
    "chapter_id": "eng_c5_ch08",
    "chapter_no": 8,
    "title": "The Decision of the Panchayat",
    "book_title": "Santoor",
    "unit_title": "Ups and Downs",
    "source_url": "https://ncert.nic.in/textbook/pdf/eesa108.pdf",
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
      "anchor_id": "eng_c5_ch08:narrative:1-5",
      "section_label": "Narrative conflict, dialogue, evidence, and resolution",
      "page_start": 1,
      "page_end": 5,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa108.pdf#page=1",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch08:language:6-8",
      "section_label": "Vocabulary, prepositions, event ordering, and word formation",
      "page_start": 6,
      "page_end": 8,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa108.pdf#page=6",
      "coverage_treatment": "taught_and_assessed",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch08:zidd-strengthening:chronology",
      "section_label": "Zidd strengthening: past-perfect chronology beyond required NCERT chapter exercises",
      "page_start": 6,
      "page_end": 8,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa108.pdf#page=6",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": false
    },
    {
      "anchor_id": "eng_c5_ch08:expression:9-10",
      "section_label": "Prediction from supplied clues and first-person letter writing",
      "page_start": 9,
      "page_end": 10,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa108.pdf#page=9",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch08:transfer:11-14",
      "section_label": "Bounded biography and independent transfer reading",
      "page_start": 11,
      "page_end": 14,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa108.pdf#page=11",
      "coverage_treatment": "textbook_companion",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch08:facilitated:9-14",
      "section_label": "Facilitated picture narration, listening, discussion, and paired comparison",
      "page_start": 9,
      "page_end": 14,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa108.pdf#page=9",
      "coverage_treatment": "guided_only",
      "required_for_chapter_certification": false
    }
  ],
  "levels": [
    {
      "level_id": "panchayat-sequence-summary",
      "title": "Follow the Conflict to Its Resolution",
      "focus": "sequence conflict, evidence, decision, and effect",
      "outcome": "Reconstruct a narrative in order and summarise its conflict, evidence check, decision, and result without copying every detail.",
      "skill_ids": [
        "reading.event_sequence",
        "writing.summary_own_words"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch08:narrative:1-5"
      ],
      "connect": {
        "teaching_block": "A dispute story is not only a list of events. Its meaning depends on how a claim is tested, how a decision follows, and what changes afterward.",
        "passage": "Two families disputed a gate. The council inspected the latch, heard both families, and assigned a shared repair. The inspection and hearing explain the final decision.",
        "prompt": "Mark the four boxes, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-sequence-summary-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
        "passage": "A farmer reports that a shared gate was locked before his cart arrived. The neighbour says the lock broke during the night. The council first inspects the broken latch, then hears both accounts, and finally asks both families to repair it together.",
        "prompt": "Which summary preserves the conflict, evidence check, and resolution in order?",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "repair first, then invent a dispute",
          "dispute, inspection and hearing, shared repair",
          "hear one family and ignore the latch",
          "describe only the cart"
        ],
        "accepted_answers": [
          "dispute, inspection and hearing, shared repair"
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "Two shopkeepers claim the same delivery crate. One shows an order slip; the other shows a receipt for a different crate number. The mediator matches both documents to the painted number and returns the crate to the first shopkeeper.",
          "prompt": "Place the evidence and decision in the correct sequence.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "documents",
                "crate number",
                "matching order",
                "decision"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "documents",
            "crate number",
            "matching order",
            "decision"
          ],
          "model_answer": "The mediator checks both documents against the crate number and then returns the crate to the shopkeeper whose order slip matches.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A school team finds a torn net after lunch. The captain accuses the morning team. The sports teacher checks the equipment log, learns that the tear was recorded before school, and clears the morning team.",
          "prompt": "What changed the course of the conflict?",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "equipment log",
                "tear before school",
                "accusation withdrawn"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "equipment log",
            "tear before school",
            "accusation withdrawn"
          ],
          "model_answer": "The equipment log showed the tear existed before the morning team played, so the accusation was withdrawn.",
          "pass_score": 0.8
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A lane floods after a wall is built. Residents first blame heavy rain. A survey shows that the new wall blocked the drain. The builder opens a channel and the water clears.",
          "prompt": "Write the cause-and-resolution sequence.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "blamed rain",
                "survey",
                "blocked drain",
                "channel opened"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "blamed rain",
            "survey",
            "blocked drain",
            "channel opened"
          ],
          "model_answer": "Residents blamed rain, but a survey identified the blocked drain; opening a channel then cleared the floodwater.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A child says her bicycle bell was taken. Another child says he found it beside the pump. A name scratched under the bell matches the first child's bicycle, so he returns it and apologises.",
          "prompt": "Which detail belongs immediately before the return?",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "scratched name",
                "matched bicycle",
                "returned"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "scratched name",
            "matched bicycle",
            "returned"
          ],
          "model_answer": "The scratched name is checked and matched to the first child's bicycle immediately before the bell is returned.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "The pond committee hears that a pipe crosses one family's field. They map the pipe, review the old permission letter, and move one section away from newly planted trees with both sides present.",
          "prompt": "Summarise the committee's method rather than only the final action.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "mapped pipe",
                "permission letter",
                "both sides",
                "moved section"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "mapped pipe",
            "permission letter",
            "both sides",
            "moved section"
          ],
          "model_answer": "The committee mapped the pipe, checked the permission record, involved both sides, and then moved the section that threatened the trees.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A class election ballot count seems wrong. The teacher seals the box, recounts with two student observers, finds three folded ballots stuck together, and announces the corrected total.",
          "prompt": "Explain why the observers appear before the corrected result.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "student observers",
                "transparent recount",
                "stuck ballots",
                "corrected total"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "student observers",
            "transparent recount",
            "stuck ballots",
            "corrected total"
          ],
          "model_answer": "The observers make the recount transparent, and the stuck ballots are found before the corrected total is announced.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A vendor claims a customer paid too little. The customer shows a written bill and payment message. The vendor adds the amounts, notices a calculation error, and corrects the bill.",
          "prompt": "Give the shortest complete ordered summary.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "compared bill",
                "addition error",
                "corrected amount"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "compared bill",
            "addition error",
            "corrected amount"
          ],
          "model_answer": "The vendor compared the bill and payment, found an addition error, and corrected the amount.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "The village path is narrowed by stacked bricks. Walkers complain, the owner explains they are for a two-day repair, and the council marks a temporary safe route with a removal deadline.",
          "prompt": "What resolution balances both needs?",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "brief repair",
                "safe route",
                "deadline",
                "public access"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "brief repair",
            "safe route",
            "deadline",
            "public access"
          ],
          "model_answer": "The bricks may remain briefly for repair, while a safe temporary route and deadline protect public access.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-sequence-summary-misconception",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "misconception": "The learner retells colourful details but loses the causal order or states a verdict without showing how evidence led to it.",
          "remediation": "Use event cards for conflict-evidence-decision-effect, then compress each card to one clause before joining them into a summary.",
          "support_check_ids": [
            "panchayat-sequence-summary-bridge",
            "panchayat-sequence-summary-masterclass",
            "panchayat-sequence-summary-revision1",
            "panchayat-sequence-summary-revision2",
            "panchayat-sequence-summary-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A farmer reports that a shared gate was locked before his cart arrived. The neighbour says the lock broke during the night. The council first inspects the broken latch, then hears both accounts, and finally asks both families to repair it together.",
          "prompt": "Which summary preserves the conflict, evidence check, and resolution in order?",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "locked gate",
                "inspected latch",
                "heard both sides",
                "shared repair"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "locked gate",
            "inspected latch",
            "heard both sides",
            "shared repair"
          ],
          "model_answer": "A locked gate caused a dispute; the council inspected the latch and heard both sides before assigning a shared repair.",
          "pass_score": 0.8
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "Two shopkeepers claim the same delivery crate. One shows an order slip; the other shows a receipt for a different crate number. The mediator matches both documents to the painted number and returns the crate to the first shopkeeper.",
          "prompt": "Place the evidence and decision in the correct sequence.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "documents",
                "crate number",
                "matching order",
                "decision"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "documents",
            "crate number",
            "matching order",
            "decision"
          ],
          "model_answer": "The mediator checks both documents against the crate number and then returns the crate to the shopkeeper whose order slip matches.",
          "pass_score": 0.8
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A school team finds a torn net after lunch. The captain accuses the morning team. The sports teacher checks the equipment log, learns that the tear was recorded before school, and clears the morning team.",
          "prompt": "What changed the course of the conflict?",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "equipment log",
                "tear before school",
                "accusation withdrawn"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "equipment log",
            "tear before school",
            "accusation withdrawn"
          ],
          "model_answer": "The equipment log showed the tear existed before the morning team played, so the accusation was withdrawn.",
          "pass_score": 0.8
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A lane floods after a wall is built. Residents first blame heavy rain. A survey shows that the new wall blocked the drain. The builder opens a channel and the water clears.",
          "prompt": "Write the cause-and-resolution sequence.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "blamed rain",
                "survey",
                "blocked drain",
                "channel opened"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "blamed rain",
            "survey",
            "blocked drain",
            "channel opened"
          ],
          "model_answer": "Residents blamed rain, but a survey identified the blocked drain; opening a channel then cleared the floodwater.",
          "pass_score": 0.8
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "panchayat-sequence-summary-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Build a four-box timeline: conflict, evidence, decision, effect; then remove details that do not change the outcome.",
          "passage": "A child says her bicycle bell was taken. Another child says he found it beside the pump. A name scratched under the bell matches the first child's bicycle, so he returns it and apologises.",
          "prompt": "Which detail belongs immediately before the return?",
          "skill_ids": [
            "reading.event_sequence",
            "writing.summary_own_words"
          ],
          "interaction_type": "summary",
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
                "scratched name",
                "matched bicycle",
                "returned"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "scratched name",
            "matched bicycle",
            "returned"
          ],
          "model_answer": "The scratched name is checked and matched to the first child's bicycle immediately before the bell is returned.",
          "pass_score": 0.8
        }
      }
    },
    {
      "level_id": "panchayat-dialogue-attribution",
      "title": "Who Said What, to Whom, and Why?",
      "focus": "track speakers, listeners, and the function of each turn",
      "outcome": "Attribute a dialogue turn to the visible speaker, identify its listener, and explain whether it makes a claim, question, evidence point, agreement, challenge, or decision.",
      "skill_ids": [
        "reading.dialogue_attribution"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch08:narrative:1-5"
      ],
      "connect": {
        "teaching_block": "Dialogue becomes evidence only when the reader tracks the exact speaker and purpose. Nearby names and hidden intentions are not reliable substitutes for visible turns.",
        "passage": "Chairperson: 'Show the receipt.' Seller: 'Here is the dated copy.' The chairperson requests evidence; the seller supplies it.",
        "prompt": "Label both turn functions, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-dialogue-attribution-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
        "passage": "Mira: 'The boundary marker moved after the rain.' Dev: 'I photographed it yesterday; let us compare the position.'",
        "prompt": "Who proposes checking evidence, and what is the purpose of that turn?",
        "skill_ids": [
          "reading.dialogue_attribution"
        ],
        "options": [
          "Mira proposes ignoring the marker",
          "Dev admits moving it",
          "Dev proposes an evidence check",
          "the rain speaks to Mira"
        ],
        "accepted_answers": [
          "Dev proposes an evidence check"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "panchayat-dialogue-attribution-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Farmer: 'The goat entered through this gap.' Neighbour: 'The gap is on my side, but the broken latch belongs to the shared gate.'",
          "prompt": "Attribute the second statement and explain what it adds.",
          "skill_ids": [
            "reading.dialogue_attribution"
          ],
          "options": [
            "the farmer accepts all blame",
            "the neighbour separates location from responsibility",
            "the gate speaks about the goat",
            "the neighbour denies there is a gap"
          ],
          "accepted_answers": [
            "the neighbour separates location from responsibility"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "panchayat-dialogue-attribution-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Chairperson: 'Each side will speak without interruption.' Rani: 'I found the receipt inside the folder.'",
          "prompt": "Which speaker sets the discussion rule?",
          "skill_ids": [
            "reading.dialogue_attribution"
          ],
          "options": [
            "Rani",
            "the chairperson",
            "the receipt",
            "an unnamed shopkeeper"
          ],
          "accepted_answers": [
            "the chairperson"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-dialogue-attribution-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Arun: 'I lent the ladder on Monday.' Saba: 'I returned it to your brother on Tuesday.' Arun's brother: 'Yes, it is in the shed.'",
          "prompt": "Track the speakers to explain where the ladder is.",
          "skill_ids": [
            "reading.dialogue_attribution"
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
                "Saba returned",
                "brother confirms",
                "shed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "Saba returned",
            "brother confirms",
            "shed"
          ],
          "model_answer": "Saba says she returned it to Arun's brother, and the brother confirms that it is in the shed.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-dialogue-attribution-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Judge: 'What result do you want?' Seller: 'Payment for the repaired wheel.' Customer: 'I will pay when the loose bolt is fixed.'",
          "prompt": "Who states a condition, and what is it?",
          "skill_ids": [
            "reading.dialogue_attribution"
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
                "customer",
                "payment condition",
                "fix loose bolt"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "customer",
            "payment condition",
            "fix loose bolt"
          ],
          "model_answer": "The customer makes payment conditional on fixing the loose bolt.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-dialogue-attribution-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Teacher: 'Which rule did both teams accept?' Captain A: 'The line itself counts as out.' Captain B: 'We agreed to that before play.'",
          "prompt": "What does Captain B's turn contribute?",
          "skill_ids": [
            "reading.dialogue_attribution"
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
                "Captain B",
                "confirms agreement",
                "before play"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "Captain B",
            "confirms agreement",
            "before play"
          ],
          "model_answer": "Captain B confirms that both teams accepted the boundary rule before play.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-dialogue-attribution-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Resident: 'The drain is blocked near house twelve.' Worker: 'I will inspect that section first.'",
          "prompt": "Who commits to an action, and why?",
          "skill_ids": [
            "reading.dialogue_attribution"
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
                "worker",
                "inspect section",
                "specific location"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "worker",
            "inspect section",
            "specific location"
          ],
          "model_answer": "The worker commits to inspecting the named section because the resident identifies a specific blockage location.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-dialogue-attribution-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Leena: 'I heard the bell at noon.' Guard: 'The maintenance log says it was tested at noon.'",
          "prompt": "How do the two turns relate?",
          "skill_ids": [
            "reading.dialogue_attribution"
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
                "observation",
                "maintenance log",
                "bell test"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "observation",
            "maintenance log",
            "bell test"
          ],
          "model_answer": "Leena reports an observation, and the guard connects it to the documented bell test.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-dialogue-attribution-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Moderator: 'Please answer the question about the path.' Witness: 'The cart used the east path after the west path flooded.'",
          "prompt": "What is the witness responding to?",
          "skill_ids": [
            "reading.dialogue_attribution"
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
                "moderator request",
                "east path",
                "west flooded"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "moderator request",
            "east path",
            "west flooded"
          ],
          "model_answer": "The witness responds to the moderator's request by identifying which path the cart used and why.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-dialogue-attribution-misconception",
          "skill_ids": [
            "reading.dialogue_attribution"
          ],
          "misconception": "The learner chooses the nearest named character as speaker or invents agreement, motive, or testimony that no visible line contains.",
          "remediation": "Use a three-column ledger for speaker, addressed person, and turn function; block any claim that cannot point to an exact line.",
          "support_check_ids": [
            "panchayat-dialogue-attribution-bridge",
            "panchayat-dialogue-attribution-masterclass",
            "panchayat-dialogue-attribution-revision1",
            "panchayat-dialogue-attribution-revision2",
            "panchayat-dialogue-attribution-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "panchayat-dialogue-attribution-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Mira: 'The boundary marker moved after the rain.' Dev: 'I photographed it yesterday; let us compare the position.'",
          "prompt": "Who proposes checking evidence, and what is the purpose of that turn?",
          "skill_ids": [
            "reading.dialogue_attribution"
          ],
          "options": [
            "Mira proposes ignoring the marker",
            "Dev admits moving it",
            "the rain speaks to Mira",
            "Dev proposes an evidence check"
          ],
          "accepted_answers": [
            "Dev proposes an evidence check"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "panchayat-dialogue-attribution-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Farmer: 'The goat entered through this gap.' Neighbour: 'The gap is on my side, but the broken latch belongs to the shared gate.'",
          "prompt": "Attribute the second statement and explain what it adds.",
          "skill_ids": [
            "reading.dialogue_attribution"
          ],
          "options": [
            "the farmer accepts all blame",
            "the gate speaks about the goat",
            "the neighbour denies there is a gap",
            "the neighbour separates location from responsibility"
          ],
          "accepted_answers": [
            "the neighbour separates location from responsibility"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "panchayat-dialogue-attribution-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Chairperson: 'Each side will speak without interruption.' Rani: 'I found the receipt inside the folder.'",
          "prompt": "Which speaker sets the discussion rule?",
          "skill_ids": [
            "reading.dialogue_attribution"
          ],
          "options": [
            "Rani",
            "the receipt",
            "the chairperson",
            "an unnamed shopkeeper"
          ],
          "accepted_answers": [
            "the chairperson"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "panchayat-dialogue-attribution-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Arun: 'I lent the ladder on Monday.' Saba: 'I returned it to your brother on Tuesday.' Arun's brother: 'Yes, it is in the shed.'",
          "prompt": "Track the speakers to explain where the ladder is.",
          "skill_ids": [
            "reading.dialogue_attribution"
          ],
          "options": [
            "Arun says he hid it",
            "the ladder returned itself",
            "Saba and the brother establish the location",
            "Monday proves it is still borrowed"
          ],
          "accepted_answers": [
            "Saba and the brother establish the location"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "panchayat-dialogue-attribution-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Write speaker, listener, and turn function beside each visible line; never assign a statement to someone who did not speak.",
          "passage": "Judge: 'What result do you want?' Seller: 'Payment for the repaired wheel.' Customer: 'I will pay when the loose bolt is fixed.'",
          "prompt": "Who states a condition, and what is it?",
          "skill_ids": [
            "reading.dialogue_attribution"
          ],
          "options": [
            "the customer: fix the bolt before payment",
            "the seller: never repair the wheel",
            "the judge: pay twice",
            "the wheel asks a question"
          ],
          "accepted_answers": [
            "the customer: fix the bolt before payment"
          ]
        }
      }
    },
    {
      "level_id": "panchayat-fairness-reasoning",
      "title": "Decide from Evidence, Not Status",
      "focus": "apply transparent fairness criteria and proportionate remedies",
      "outcome": "Write a reasoned decision that hears relevant sides, tests evidence, names the principle used, and proposes a remedy proportionate to the actual harm.",
      "skill_ids": [
        "reading.inference_reason",
        "writing.reason_answer"
      ],
      "episode_kind": "application_mission",
      "source_anchor_ids": [
        "eng_c5_ch08:narrative:1-5"
      ],
      "connect": {
        "teaching_block": "Fairness is not automatic sameness. A trustworthy decision considers relevant circumstances, uses evidence openly, avoids conflicts of interest, and explains why the remedy fits.",
        "passage": "One learner missed class because a recorded bus breakdown delayed the route. Others left home late. Recording all absences is equal; responding to the verified cause makes the decision fair.",
        "prompt": "Name the common rule and the relevant difference, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-fairness-reasoning-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
        "passage": "Two children claim a found compass. Asha describes a crack near the hinge before seeing it; Nikhil says only that he likes blue. The compass has the crack Asha named.",
        "prompt": "Decide the claim fairly and explain the strongest evidence.",
        "skill_ids": [
          "reading.inference_reason"
        ],
        "options": [
          "Nikhil, because he likes blue",
          "both, without checking evidence",
          "neither, because compasses have hinges",
          "Asha, because she knew the hidden crack"
        ],
        "accepted_answers": [
          "Asha, because she knew the hidden crack"
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "Policy card: Record every late arrival. Do not give a late slip when a verified transport breakdown caused the delay; give a late slip when a student left home late. Three students arrive late: one student's bus had a recorded breakdown, while the other two say they left home late.",
          "prompt": "Apply the policy card to propose a fair response without confusing equality with fairness.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "record",
              "description": "Records every late arrival as the policy requires.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "exception",
              "description": "Withholds a late slip for the verified transport breakdown.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "rule",
              "description": "Issues late slips to students who left home late.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "record",
              "description": "Records every late arrival as the policy requires.",
              "any_of": [
                "record all three late arrivals"
              ]
            },
            {
              "id": "exception",
              "description": "Withholds a late slip for the verified transport breakdown.",
              "any_of": [
                "do not issue a late slip to the student whose bus had the verified breakdown"
              ]
            },
            {
              "id": "rule",
              "description": "Issues late slips to students who left home late.",
              "any_of": [
                "issue late slips to the two students who left home late"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "record all three late arrivals",
            "verified transport breakdown",
            "do not issue a late slip",
            "two students who left home late",
            "issue late slips"
          ],
          "model_answer": "Record all three late arrivals. Do not issue a late slip to the student whose bus had the verified breakdown, because the policy excuses that delay. Issue late slips to the two students who left home late, as the policy directs.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "Two lanes share a pump. The upper lane used it for two hours beyond its agreed time after a fire emergency. The lower lane lost access but also received water from the emergency tanker.",
          "prompt": "Write a balanced resolution using the emergency evidence and future access.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "context",
              "description": "Recognises the verified emergency.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "balance",
              "description": "Accounts for actual lost and replacement access.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "future",
              "description": "Adds a process improvement.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "context",
              "description": "Recognises the verified emergency.",
              "any_of": [
                "fire emergency",
                "extra use"
              ]
            },
            {
              "id": "balance",
              "description": "Accounts for actual lost and replacement access.",
              "any_of": [
                "tanker",
                "next scheduled turn"
              ]
            },
            {
              "id": "future",
              "description": "Adds a process improvement.",
              "any_of": [
                "notification rule"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "fire emergency",
            "extra use",
            "tanker",
            "next scheduled turn",
            "notification rule"
          ],
          "model_answer": "Recognise that the extra use responded to a fire, confirm the tanker support already received, and restore the lower lane's next scheduled turn. Add an emergency-notification rule for future cases.",
          "pass_score": 0.8
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "A football lands on a garden bed and breaks two seedlings. The player admits the kick was accidental and offers to replace them. The gardener asks to ban all games from the entire field.",
          "prompt": "Recommend a proportionate decision with a reason.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "repair",
              "description": "Addresses actual harm.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "prevention",
              "description": "Gives a targeted future step.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "proportion",
              "description": "Explains why total ban is excessive.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "repair",
              "description": "Addresses actual harm.",
              "any_of": [
                "replace seedlings"
              ]
            },
            {
              "id": "prevention",
              "description": "Gives a targeted future step.",
              "any_of": [
                "move boundary",
                "away from garden"
              ]
            },
            {
              "id": "proportion",
              "description": "Explains why total ban is excessive.",
              "any_of": [
                "disproportionate",
                "narrower step"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "replace seedlings",
            "move boundary",
            "away from garden",
            "disproportionate",
            "narrower step"
          ],
          "model_answer": "The player should replace the damaged seedlings and the play boundary should move away from the garden. A total field ban is disproportionate when a narrower preventive step addresses the harm.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "A council member is related to one person in a property dispute. The relationship is disclosed before discussion.",
          "prompt": "What process protects trust in the decision?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "conflict",
              "description": "Recognises the relationship conflict.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "replacement",
              "description": "Uses an uninvolved decision-maker.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "record",
              "description": "Requires reasoned transparency.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "conflict",
              "description": "Recognises the relationship conflict.",
              "any_of": [
                "related member",
                "not decide"
              ]
            },
            {
              "id": "replacement",
              "description": "Uses an uninvolved decision-maker.",
              "any_of": [
                "uninvolved member"
              ]
            },
            {
              "id": "record",
              "description": "Requires reasoned transparency.",
              "any_of": [
                "record reasons",
                "evidence"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "related member",
            "not decide",
            "uninvolved member",
            "record reasons",
            "evidence"
          ],
          "model_answer": "The related member should not decide the case; an uninvolved member should hear the evidence and record the reasons.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "A shop scale gives a different weight on repeated checks. The buyer wants a refund; the seller says the packet was sealed.",
          "prompt": "Describe the evidence-first resolution.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "test",
              "description": "Checks the disputed instrument.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "verify",
              "description": "Uses a reliable reweighing.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Connects result to remedy.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "test",
              "description": "Checks the disputed instrument.",
              "any_of": [
                "standard weight",
                "test scale"
              ]
            },
            {
              "id": "verify",
              "description": "Uses a reliable reweighing.",
              "any_of": [
                "verified scale",
                "sealed packet"
              ]
            },
            {
              "id": "decision",
              "description": "Connects result to remedy.",
              "any_of": [
                "correct payment",
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
            "standard weight",
            "test scale",
            "verified scale",
            "sealed packet",
            "correct payment",
            "confirm"
          ],
          "model_answer": "Test the scale with a standard weight, reweigh the sealed packet on a verified scale, and then correct the payment or confirm it based on the reliable result.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "Four group members prepared a project. The final speaker receives all the praise, but the work log shows research, drawing, writing, and rehearsal were shared.",
          "prompt": "Make a fair recognition decision using the log.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "evidence",
              "description": "Uses the work log.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "recognition",
              "description": "Credits each contribution.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "boundary",
              "description": "Keeps presentation credit proportionate.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "evidence",
              "description": "Uses the work log.",
              "any_of": [
                "work log",
                "shared"
              ]
            },
            {
              "id": "recognition",
              "description": "Credits each contribution.",
              "any_of": [
                "research",
                "drawing",
                "writing",
                "rehearsal"
              ]
            },
            {
              "id": "boundary",
              "description": "Keeps presentation credit proportionate.",
              "any_of": [
                "speaker role",
                "not all credit"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "work log",
            "shared",
            "research",
            "drawing",
            "writing",
            "rehearsal",
            "speaker role",
            "not all credit"
          ],
          "model_answer": "Recognise each member's documented contribution and also note the final speaker's presentation role. The visible speaker should not receive credit for all shared work.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "A water bill rises sharply. One family is blamed because its house is closest to the meter. A plumber later finds a leak in the pipe before it branches to any house.",
          "prompt": "Revise the blame using the new evidence.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "revision",
              "description": "Withdraws unsupported blame.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "repair",
              "description": "Addresses the shared cause.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "followup",
              "description": "Requires later evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "revision",
              "description": "Withdraws unsupported blame.",
              "any_of": [
                "location not proof",
                "withdraw blame"
              ]
            },
            {
              "id": "repair",
              "description": "Addresses the shared cause.",
              "any_of": [
                "shared pipe",
                "repair"
              ]
            },
            {
              "id": "followup",
              "description": "Requires later evidence.",
              "any_of": [
                "compare readings",
                "before responsibility"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "location not proof",
            "withdraw blame",
            "shared pipe",
            "repair",
            "compare readings",
            "before responsibility"
          ],
          "model_answer": "Withdraw the blame because location alone did not prove use. Repair the shared pipe and compare later readings before assigning any household responsibility.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "A teacher hears only the loudest student's complaint about a group task. Two quieter students have dated notes showing a different sequence of events.",
          "prompt": "What should happen before a decision?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voices",
              "description": "Includes all affected students.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Checks dated notes.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "synthesis",
              "description": "Compares accounts before decision.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voices",
              "description": "Includes all affected students.",
              "any_of": [
                "hear each student"
              ]
            },
            {
              "id": "evidence",
              "description": "Checks dated notes.",
              "any_of": [
                "dated notes",
                "review"
              ]
            },
            {
              "id": "synthesis",
              "description": "Compares accounts before decision.",
              "any_of": [
                "agreement",
                "conflict",
                "before deciding"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "hear each student",
            "dated notes",
            "review",
            "agreement",
            "conflict",
            "before deciding"
          ],
          "model_answer": "The teacher should hear each student, review the dated notes, and summarise points of agreement and conflict before deciding.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-fairness-reasoning-misconception",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "misconception": "The learner treats fairness as identical outcomes, accepts the loudest claim, or proposes punishment before testing evidence and proportionality.",
          "remediation": "Fill a decision frame in order: voices heard, claim, verified evidence, principle, remedy, and remaining uncertainty.",
          "support_check_ids": [
            "panchayat-fairness-reasoning-bridge",
            "panchayat-fairness-reasoning-masterclass",
            "panchayat-fairness-reasoning-revision1",
            "panchayat-fairness-reasoning-revision2",
            "panchayat-fairness-reasoning-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "Two children claim a found compass. Asha describes a crack near the hinge before seeing it; Nikhil says only that he likes blue. The compass has the crack Asha named.",
          "prompt": "Decide the claim fairly and explain the strongest evidence.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "decision",
              "description": "States the supported decision.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Uses the distinctive prior detail.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "contrast",
              "description": "Rejects irrelevant evidence.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "decision",
              "description": "States the supported decision.",
              "any_of": [
                "Asha stronger claim"
              ]
            },
            {
              "id": "evidence",
              "description": "Uses the distinctive prior detail.",
              "any_of": [
                "hidden crack",
                "before seeing"
              ]
            },
            {
              "id": "contrast",
              "description": "Rejects irrelevant evidence.",
              "any_of": [
                "colour preference",
                "not ownership"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "Asha stronger claim",
            "hidden crack",
            "before seeing",
            "colour preference",
            "not ownership"
          ],
          "model_answer": "Asha has the stronger claim because she identifies a hidden crack before inspecting the compass. Nikhil's colour preference does not show ownership.",
          "pass_score": 0.8
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "A class monitor gives late slips to three students. One bus was delayed by a recorded breakdown; two students left home late by their own account.",
          "prompt": "Propose a fair response without confusing equality with fairness.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "record",
              "description": "Applies a common factual record.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "exception",
              "description": "Uses verified circumstance.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "rule",
              "description": "Applies the normal rule where relevant.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "record",
              "description": "Applies a common factual record.",
              "any_of": [
                "record arrivals"
              ]
            },
            {
              "id": "exception",
              "description": "Uses verified circumstance.",
              "any_of": [
                "bus breakdown",
                "excuse"
              ]
            },
            {
              "id": "rule",
              "description": "Applies the normal rule where relevant.",
              "any_of": [
                "other two",
                "normal late rule"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "record arrivals",
            "bus breakdown",
            "excuse",
            "other two",
            "normal late rule"
          ],
          "model_answer": "Record all three arrivals, but excuse the student affected by the verified bus breakdown and apply the normal late rule to the other two. The relevant circumstances are different.",
          "pass_score": 0.8
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "Two lanes share a pump. The upper lane used it for two hours beyond its agreed time after a fire emergency. The lower lane lost access but also received water from the emergency tanker.",
          "prompt": "Write a balanced resolution using the emergency evidence and future access.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "context",
              "description": "Recognises the verified emergency.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "balance",
              "description": "Accounts for actual lost and replacement access.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "future",
              "description": "Adds a process improvement.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "context",
              "description": "Recognises the verified emergency.",
              "any_of": [
                "fire emergency",
                "extra use"
              ]
            },
            {
              "id": "balance",
              "description": "Accounts for actual lost and replacement access.",
              "any_of": [
                "tanker",
                "next scheduled turn"
              ]
            },
            {
              "id": "future",
              "description": "Adds a process improvement.",
              "any_of": [
                "notification rule"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "fire emergency",
            "extra use",
            "tanker",
            "next scheduled turn",
            "notification rule"
          ],
          "model_answer": "Recognise that the extra use responded to a fire, confirm the tanker support already received, and restore the lower lane's next scheduled turn. Add an emergency-notification rule for future cases.",
          "pass_score": 0.8
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "A football lands on a garden bed and breaks two seedlings. The player admits the kick was accidental and offers to replace them. The gardener asks to ban all games from the entire field.",
          "prompt": "Recommend a proportionate decision with a reason.",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "repair",
              "description": "Addresses actual harm.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "prevention",
              "description": "Gives a targeted future step.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "proportion",
              "description": "Explains why total ban is excessive.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "repair",
              "description": "Addresses actual harm.",
              "any_of": [
                "replace seedlings"
              ]
            },
            {
              "id": "prevention",
              "description": "Gives a targeted future step.",
              "any_of": [
                "move boundary",
                "away from garden"
              ]
            },
            {
              "id": "proportion",
              "description": "Explains why total ban is excessive.",
              "any_of": [
                "disproportionate",
                "narrower step"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "replace seedlings",
            "move boundary",
            "away from garden",
            "disproportionate",
            "narrower step"
          ],
          "model_answer": "The player should replace the damaged seedlings and the play boundary should move away from the garden. A total field ban is disproportionate when a narrower preventive step addresses the harm.",
          "pass_score": 0.8
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "panchayat-fairness-reasoning-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Separate claim, evidence, principle, and remedy; reject status, loudness, and preference when they do not prove the claim.",
          "passage": "A council member is related to one person in a property dispute. The relationship is disclosed before discussion.",
          "prompt": "What process protects trust in the decision?",
          "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "conflict",
              "description": "Recognises the relationship conflict.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "replacement",
              "description": "Uses an uninvolved decision-maker.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "record",
              "description": "Requires reasoned transparency.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "conflict",
              "description": "Recognises the relationship conflict.",
              "any_of": [
                "related member",
                "not decide"
              ]
            },
            {
              "id": "replacement",
              "description": "Uses an uninvolved decision-maker.",
              "any_of": [
                "uninvolved member"
              ]
            },
            {
              "id": "record",
              "description": "Requires reasoned transparency.",
              "any_of": [
                "record reasons",
                "evidence"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "related member",
            "not decide",
            "uninvolved member",
            "record reasons",
            "evidence"
          ],
          "model_answer": "The related member should not decide the case; an uninvolved member should hear the evidence and record the reasons.",
          "pass_score": 0.8
        }
      }
    },
    {
      "level_id": "panchayat-language-relations",
      "title": "Meaning and Relationship in Context",
      "focus": "infer chapter vocabulary and choose precise prepositions",
      "outcome": "Use surrounding definitions, actions, and contrasts to infer vocabulary, and select prepositions that express the intended place, movement, time, or relationship.",
      "skill_ids": [
        "reading.word_meaning_context",
        "grammar.prepositions"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch08:language:6-8"
      ],
      "connect": {
        "teaching_block": "Prepositions are small relationship words, while unfamiliar vocabulary is unlocked by nearby definitions, actions, contrasts, and results. Both require reading beyond the blank or target word.",
        "passage": "The witness stood before the chairperson and placed the record on the table. 'Before' shows position; 'on' shows surface contact.",
        "prompt": "Name both relationships, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-language-relations-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
        "passage": "The council met ___ the banyan tree and spoke ___ the two families.",
        "prompt": "Choose the pair of prepositions that expresses place and relationship accurately.",
        "skill_ids": [
          "reading.word_meaning_context",
          "grammar.prepositions"
        ],
        "options": [
          "between; at",
          "under; with",
          "during; through",
          "from; into"
        ],
        "accepted_answers": [
          "under; with"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "panchayat-language-relations-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The notice remained ___ the wall ___ Monday ___ Friday.",
          "prompt": "Fill the place, starting-point, and ending-point relationships.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
          ],
          "options": [
            "in; between; at",
            "over; by; through",
            "with; into; for",
            "on; from; to"
          ],
          "accepted_answers": [
            "on; from; to"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "panchayat-language-relations-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The word 'verdict' appears after both sides are heard and names the final decision.",
          "prompt": "Use context to select the meaning of 'verdict'.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
          ],
          "options": [
            "the opening complaint",
            "a person who speaks first",
            "the final decision",
            "a path between houses"
          ],
          "accepted_answers": [
            "the final decision"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-language-relations-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The witness walked ___ the gate, stood ___ the chairperson, and placed the letter ___ the table.",
          "prompt": "Choose the direction, position, and surface prepositions.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
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
                "through",
                "before",
                "on"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "through",
            "before",
            "on"
          ],
          "model_answer": "The witness walked through the gate, stood before the chairperson, and placed the letter on the table.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-language-relations-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "In this sentence, 'claim' means a statement that something belongs to someone or is true; it does not yet mean the statement is proved.",
          "prompt": "Explain the difference between a claim and evidence.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
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
                "claim statement",
                "evidence tests",
                "not proved"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "claim statement",
            "evidence tests",
            "not proved"
          ],
          "model_answer": "A claim is what a person says is true, while evidence is information used to test that statement.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-language-relations-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The neighbours divided the repair cost ___ themselves because the wall stood ___ both houses.",
          "prompt": "Complete the group and position relationships.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
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
                "among",
                "between",
                "relationship"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "among",
            "between",
            "relationship"
          ],
          "model_answer": "The neighbours divided the cost among themselves because the wall stood between both houses.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-language-relations-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The word 'impartial' describes a decision-maker who does not favour either side.",
          "prompt": "Use the clue to explain 'impartial' in your own words.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
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
                "without favour",
                "either side",
                "judge fairly"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "without favour",
            "either side",
            "judge fairly"
          ],
          "model_answer": "Impartial means judging without giving unfair preference to either side.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-language-relations-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The children waited ___ the hearing, then walked ___ the room when their names were called.",
          "prompt": "Choose the time and movement prepositions.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
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
                "outside",
                "into",
                "movement"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "outside",
            "into",
            "movement"
          ],
          "model_answer": "The children waited outside the hearing room, then walked into the room when called.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-language-relations-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "A 'testimony' is an account given by a witness. It may be checked against records and other evidence.",
          "prompt": "Which statement uses testimony accurately?",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
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
                "witness account",
                "compared with register"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "witness account",
            "compared with register"
          ],
          "model_answer": "The witness's testimony described what she saw, and the council compared it with the register.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-language-relations-misconception",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
          ],
          "misconception": "The learner swaps familiar prepositions freely or chooses a vocabulary meaning from sound without checking the surrounding event.",
          "remediation": "Sort the needed relationship as place, movement, time, or connection, and run a full-sentence substitution test for every proposed meaning.",
          "support_check_ids": [
            "panchayat-language-relations-bridge",
            "panchayat-language-relations-masterclass",
            "panchayat-language-relations-revision1",
            "panchayat-language-relations-revision2",
            "panchayat-language-relations-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "panchayat-language-relations-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The council met ___ the banyan tree and spoke ___ the two families.",
          "prompt": "Choose the pair of prepositions that expresses place and relationship accurately.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
          ],
          "options": [
            "between; at",
            "under; with",
            "during; through",
            "from; into"
          ],
          "accepted_answers": [
            "under; with"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "panchayat-language-relations-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The notice remained ___ the wall ___ Monday ___ Friday.",
          "prompt": "Fill the place, starting-point, and ending-point relationships.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
          ],
          "options": [
            "in; between; at",
            "on; from; to",
            "over; by; through",
            "with; into; for"
          ],
          "accepted_answers": [
            "on; from; to"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "panchayat-language-relations-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The word 'verdict' appears after both sides are heard and names the final decision.",
          "prompt": "Use context to select the meaning of 'verdict'.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
          ],
          "options": [
            "the opening complaint",
            "the final decision",
            "a person who speaks first",
            "a path between houses"
          ],
          "accepted_answers": [
            "the final decision"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "panchayat-language-relations-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "The witness walked ___ the gate, stood ___ the chairperson, and placed the letter ___ the table.",
          "prompt": "Choose the direction, position, and surface prepositions.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
          ],
          "options": [
            "at; during; into",
            "under; from; with",
            "beside; across; among",
            "through; before; on"
          ],
          "accepted_answers": [
            "through; before; on"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "panchayat-language-relations-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Name the relationship first for a preposition; for vocabulary, substitute the possible meaning into the whole sentence.",
          "passage": "In this sentence, 'claim' means a statement that something belongs to someone or is true; it does not yet mean the statement is proved.",
          "prompt": "Explain the difference between a claim and evidence.",
          "skill_ids": [
            "reading.word_meaning_context",
            "grammar.prepositions"
          ],
          "options": [
            "two words for the same proof",
            "a statement versus information that tests it",
            "a claim is always a final verdict",
            "evidence means a personal preference"
          ],
          "accepted_answers": [
            "a statement versus information that tests it"
          ]
        }
      }
    },
    {
      "level_id": "panchayat-past-chronology",
      "title": "Strengthening: Show Which Past Event Happened First",
      "focus": "strengthen chronology by using past perfect and simple past together",
      "outcome": "As extra Zidd strengthening, use had plus a past participle for an earlier completed past event when a later simple-past event provides the reference point.",
      "skill_ids": [
        "grammar.tense_usage"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch08:zidd-strengthening:chronology"
      ],
      "connect": {
        "teaching_block": "Past perfect is useful when two events are already in the past and their order matters. It is not formed with has or have, and sentence position alone does not determine which event came first.",
        "passage": "The council had read the letter before it announced the decision. Reading happened first; announcing happened later.",
        "prompt": "Point to the earlier and later verbs, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-past-chronology-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
        "passage": "The council had examined the map before it announced the boundary.",
        "prompt": "Which event happened first?",
        "skill_ids": [
          "grammar.tense_usage"
        ],
        "options": [
          "examining the map",
          "announcing the boundary",
          "both at exactly the same time",
          "drawing a new map later"
        ],
        "accepted_answers": [
          "examining the map"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "panchayat-past-chronology-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "By the time the farmer arrived, the clerk had opened the record room.",
          "prompt": "Explain the time relationship expressed by 'had opened'.",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "opening happened after arrival",
            "opening happened earlier",
            "the room is still closed",
            "the farmer opened the room"
          ],
          "accepted_answers": [
            "opening happened earlier"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "panchayat-past-chronology-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "The witness had left when the messenger reached the hall.",
          "prompt": "Rewrite the meaning as two ordered events.",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "messenger arrived, then witness left",
            "both never reached the hall",
            "the hall left first",
            "witness left, then messenger arrived"
          ],
          "accepted_answers": [
            "witness left, then messenger arrived"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-past-chronology-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "After the panch had heard both sides, she asked for the document.",
          "prompt": "Why is past perfect used for hearing?",
          "skill_ids": [
            "grammar.tense_usage"
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
                "had heard",
                "completed before",
                "asked later"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "had heard",
            "completed before",
            "asked later"
          ],
          "model_answer": "Past perfect marks hearing both sides as completed before the later request for the document.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-past-chronology-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "The shopkeeper corrected the bill after he had checked the receipt.",
          "prompt": "Choose the accurate event order.",
          "skill_ids": [
            "grammar.tense_usage"
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
                "had checked",
                "corrected after"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "had checked",
            "corrected after"
          ],
          "model_answer": "He checked the receipt first and corrected the bill second.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-past-chronology-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "Before the rain began, workers had covered the open grain sacks.",
          "prompt": "Write one sentence explaining the protective sequence.",
          "skill_ids": [
            "grammar.tense_usage"
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
                "had covered",
                "before rain",
                "protected"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "had covered",
            "before rain",
            "protected"
          ],
          "model_answer": "The workers had covered the sacks before rain began, so the grain was protected first.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-past-chronology-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "The children found the key after the caretaker had searched the office.",
          "prompt": "Which action belongs to the earlier time?",
          "skill_ids": [
            "grammar.tense_usage"
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
                "had searched",
                "before found"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "had searched",
            "before found"
          ],
          "model_answer": "The caretaker's office search happened before the children found the key.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-past-chronology-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "When the hearing started, the secretary had already numbered the papers.",
          "prompt": "Explain what 'already' reinforces.",
          "skill_ids": [
            "grammar.tense_usage"
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
                "already",
                "numbering complete",
                "before hearing"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "already",
            "numbering complete",
            "before hearing"
          ],
          "model_answer": "It reinforces that numbering was complete before the hearing started.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-past-chronology-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "The bus had departed before Lina reached the stop.",
          "prompt": "Write the two events in chronological order.",
          "skill_ids": [
            "grammar.tense_usage"
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
                "bus departed first",
                "Lina reached later"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "bus departed first",
            "Lina reached later"
          ],
          "model_answer": "First the bus departed; then Lina reached the stop.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-past-chronology-misconception",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "misconception": "The learner uses has or have for past perfect, chooses tense from clause order, or fails to distinguish earlier and later past events.",
          "remediation": "Draw a two-point timeline, label earlier and later, build had plus past participle for earlier, and use simple past for the reference event.",
          "support_check_ids": [
            "panchayat-past-chronology-bridge",
            "panchayat-past-chronology-masterclass",
            "panchayat-past-chronology-revision1",
            "panchayat-past-chronology-revision2",
            "panchayat-past-chronology-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "panchayat-past-chronology-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "The council had examined the map before it announced the boundary.",
          "prompt": "Which event happened first?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "announcing the boundary",
            "both at exactly the same time",
            "drawing a new map later",
            "examining the map"
          ],
          "accepted_answers": [
            "examining the map"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "panchayat-past-chronology-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "By the time the farmer arrived, the clerk had opened the record room.",
          "prompt": "Explain the time relationship expressed by 'had opened'.",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "opening happened after arrival",
            "the room is still closed",
            "the farmer opened the room",
            "opening happened earlier"
          ],
          "accepted_answers": [
            "opening happened earlier"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "panchayat-past-chronology-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "The witness had left when the messenger reached the hall.",
          "prompt": "Rewrite the meaning as two ordered events.",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "messenger arrived, then witness left",
            "both never reached the hall",
            "the hall left first",
            "witness left, then messenger arrived"
          ],
          "accepted_answers": [
            "witness left, then messenger arrived"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "panchayat-past-chronology-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "After the panch had heard both sides, she asked for the document.",
          "prompt": "Why is past perfect used for hearing?",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "hearing was completed before asking",
            "hearing will happen tomorrow",
            "the document heard both sides",
            "asking happened first"
          ],
          "accepted_answers": [
            "hearing was completed before asking"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "panchayat-past-chronology-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Place both events on a timeline before selecting the verb forms; earlier completed event gets had plus participle.",
          "passage": "The shopkeeper corrected the bill after he had checked the receipt.",
          "prompt": "Choose the accurate event order.",
          "skill_ids": [
            "grammar.tense_usage"
          ],
          "options": [
            "correct bill, then check receipt",
            "do both in the future",
            "check receipt, then correct bill",
            "never inspect the receipt"
          ],
          "accepted_answers": [
            "check receipt, then correct bill"
          ]
        }
      }
    },
    {
      "level_id": "panchayat-clue-prediction",
      "title": "Predict Only What the Clues Support",
      "focus": "identify a main situation and answer with a cautious evidence-based prediction",
      "outcome": "State the central situation in a supplied written scene, make a plausible prediction, and support it with visible clues while marking uncertainty.",
      "skill_ids": [
        "reading.paragraph_main_idea",
        "writing.short_answer"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch08:expression:9-10"
      ],
      "connect": {
        "teaching_block": "The chapter includes picture prediction. Here, written scene cards let you practise the same clue-based inference when an image is not shown.",
        "passage": "Clues: dark clouds, clothes on a line, and a basket carried outside. A supported prediction is that someone may collect the clothes before rain.",
        "prompt": "Identify the prediction and its two clues, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-clue-prediction-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
        "passage": "Visible text-card clues: muddy footprints lead from the open gate to an empty feed bowl; the dog is not in its shelter.",
        "prompt": "Make one plausible prediction and cite two clues.",
        "skill_ids": [
          "reading.paragraph_main_idea"
        ],
        "options": [
          "the dog may have left through the gate",
          "a bird certainly stole the shelter",
          "the bowl proves it never contained food",
          "the dog is invisible forever"
        ],
        "accepted_answers": [
          "the dog may have left through the gate"
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: a bicycle lies beside a path, its chain is off the wheel, and a child is walking toward a repair stall.",
          "prompt": "What is the most supported next event?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "chain off",
                "repair stall",
                "ask for help"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "chain off",
            "repair stall",
            "ask for help"
          ],
          "model_answer": "The child will probably ask for help repairing the bicycle chain at the nearby stall.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: dark clouds gather, clothes remain on a line, and a woman hurries outside carrying a basket.",
          "prompt": "Predict her immediate action with evidence.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "collect clothes",
                "dark clouds",
                "basket"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "collect clothes",
            "dark clouds",
            "basket"
          ],
          "model_answer": "She will probably collect the clothes before rain because clouds are dark and she carries a basket toward the line.",
          "pass_score": 0.8
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: two students hold the same certificate, one name is crossed out, and the teacher is checking the printed list.",
          "prompt": "Write a cautious prediction rather than a certainty.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "verify certificate",
                "crossed name",
                "printed list",
                "may"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "verify certificate",
            "crossed name",
            "printed list",
            "may"
          ],
          "model_answer": "The teacher may verify whose certificate was printed incorrectly by comparing the names with the list.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: a classroom plant droops, the soil is dry below the surface, and a watering can is full beside it.",
          "prompt": "What action is supported, and what result is only a prediction?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "water plant",
                "dry soil",
                "firmer later",
                "not guaranteed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "water plant",
            "dry soil",
            "firmer later",
            "not guaranteed"
          ],
          "model_answer": "Watering the plant is supported by the dry soil; the plant becoming firmer later is a reasonable prediction, not a guaranteed fact.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: the library door is open, lights are on, and a sign says 'Story circle, 3:30'. The clock shows 3:25.",
          "prompt": "Predict what will likely happen next.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "story circle",
                "3:30",
                "3:25",
                "room prepared"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "story circle",
            "3:30",
            "3:25",
            "room prepared"
          ],
          "model_answer": "Children will likely arrive or gather for the story circle because the room is prepared five minutes before the announced time.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: a package is wet on one corner, the porch roof has a gap, and fresh rainwater lies below that gap.",
          "prompt": "Infer the likely cause without claiming more than the clues show.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "rain",
                "roof gap",
                "wet corner",
                "probably"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "rain",
            "roof gap",
            "wet corner",
            "probably"
          ],
          "model_answer": "Rain probably passed through the roof gap and wet the package corner below it.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: a team studies a rulebook, the scoreboard is paused, and both captains stand beside the referee.",
          "prompt": "What is the likely purpose of the pause?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "rulebook",
                "paused score",
                "captains",
                "checking dispute"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "rulebook",
            "paused score",
            "captains",
            "checking dispute"
          ],
          "model_answer": "They are likely checking a disputed rule before play and scoring continue.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "A sound prediction names a likely event, cites visible clues, uses cautious language when evidence is incomplete, and avoids invented motives or outcomes.",
          "prompt": "State the prediction checklist.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "may happen",
                "supporting clues",
                "cautious language",
                "no hidden motives"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "may happen",
            "supporting clues",
            "cautious language",
            "no hidden motives"
          ],
          "model_answer": "Say what may happen, point to the clues that support it, use words such as likely or may, and do not invent hidden intentions.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-clue-prediction-misconception",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
          ],
          "misconception": "The learner states a certainty, invents unseen details or motives, or repeats one clue without connecting it to a likely event.",
          "remediation": "Use the frame 'Because clue one and clue two, ___ may happen'; cross out every detail not present in the supplied card.",
          "support_check_ids": [
            "panchayat-clue-prediction-bridge",
            "panchayat-clue-prediction-masterclass",
            "panchayat-clue-prediction-revision1",
            "panchayat-clue-prediction-revision2",
            "panchayat-clue-prediction-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Visible text-card clues: muddy footprints lead from the open gate to an empty feed bowl; the dog is not in its shelter.",
          "prompt": "Make one plausible prediction and cite two clues.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "dog went through gate",
                "footprints",
                "open gate",
                "empty bowl"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "dog went through gate",
            "footprints",
            "open gate",
            "empty bowl"
          ],
          "model_answer": "The dog may have gone through the open gate because its footprints lead away and its feed bowl is empty near the trail.",
          "pass_score": 0.8
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: a bicycle lies beside a path, its chain is off the wheel, and a child is walking toward a repair stall.",
          "prompt": "What is the most supported next event?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "chain off",
                "repair stall",
                "ask for help"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "chain off",
            "repair stall",
            "ask for help"
          ],
          "model_answer": "The child will probably ask for help repairing the bicycle chain at the nearby stall.",
          "pass_score": 0.8
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: dark clouds gather, clothes remain on a line, and a woman hurries outside carrying a basket.",
          "prompt": "Predict her immediate action with evidence.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "collect clothes",
                "dark clouds",
                "basket"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "collect clothes",
            "dark clouds",
            "basket"
          ],
          "model_answer": "She will probably collect the clothes before rain because clouds are dark and she carries a basket toward the line.",
          "pass_score": 0.8
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: two students hold the same certificate, one name is crossed out, and the teacher is checking the printed list.",
          "prompt": "Write a cautious prediction rather than a certainty.",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "verify certificate",
                "crossed name",
                "printed list",
                "may"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "verify certificate",
            "crossed name",
            "printed list",
            "may"
          ],
          "model_answer": "The teacher may verify whose certificate was printed incorrectly by comparing the names with the list.",
          "pass_score": 0.8
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "panchayat-clue-prediction-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Name the situation, choose two supplied clues, and use may, likely, or probably when the outcome is not certain.",
          "passage": "Clues: a classroom plant droops, the soil is dry below the surface, and a watering can is full beside it.",
          "prompt": "What action is supported, and what result is only a prediction?",
          "skill_ids": [
            "reading.paragraph_main_idea",
            "writing.short_answer"
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
                "water plant",
                "dry soil",
                "firmer later",
                "not guaranteed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "water plant",
            "dry soil",
            "firmer later",
            "not guaranteed"
          ],
          "model_answer": "Watering the plant is supported by the dry soil; the plant becoming firmer later is a reasonable prediction, not a guaranteed fact.",
          "pass_score": 0.8
        }
      }
    },
    {
      "level_id": "panchayat-first-person-letter",
      "title": "Write from the Affected Person's View",
      "focus": "respond to a decision in a coherent first-person letter",
      "outcome": "Write a focused first-person letter with greeting, accurate decision/evidence reference, personal effect, relevant next request, connected paragraph, and closing.",
      "skill_ids": [
        "grammar.punctuation_capitalization",
        "writing.friendly_message",
        "writing.paragraph"
      ],
      "episode_kind": "expression_workshop",
      "source_anchor_ids": [
        "eng_c5_ch08:expression:9-10"
      ],
      "connect": {
        "teaching_block": "A first-person letter is not a neutral retelling. It shows how a decision affects the writer while staying faithful to known events and addressing a real reader with a clear purpose.",
        "passage": "Dear Council Secretary, I accept the shared repair decision. Please confirm Friday's meeting time so both families can attend. Yours, Rina.",
        "prompt": "Mark role, decision, request, greeting, and closing, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-first-person-letter-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
        "passage": "Role: the farmer whose seedlings were damaged. Decision: the player will replace them and the boundary will move.",
        "prompt": "Write a first-person letter to the council responding to the decision.",
        "skill_ids": [
          "grammar.punctuation_capitalization"
        ],
        "options": [
          "write as the council",
          "omit the decision",
          "farmer accepts replacement and asks about boundary timing",
          "copy an unrelated complaint"
        ],
        "accepted_answers": [
          "farmer accepts replacement and asks about boundary timing"
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: a student wrongly blamed for a torn net. Evidence: the log showed the tear existed before school.",
          "prompt": "Write a short letter to the sports teacher after the finding.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the student's first-person experience.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Mentions the earlier log.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "Suggests a relevant improvement.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the student's first-person experience.",
              "any_of": [
                "my team",
                "I felt",
                "we were blamed"
              ]
            },
            {
              "id": "evidence",
              "description": "Mentions the earlier log.",
              "any_of": [
                "equipment log",
                "earlier record"
              ]
            },
            {
              "id": "next",
              "description": "Suggests a relevant improvement.",
              "any_of": [
                "check the log",
                "future"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear",
                "Yours"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "my team",
            "I felt",
            "we were blamed",
            "equipment log",
            "earlier record",
            "check the log",
            "future",
            "Dear"
          ],
          "model_answer": "Dear Ma'am, Thank you for checking the equipment log and clearing my team. I felt worried when we were blamed, but the earlier record showed what happened. Could the class check the log before future accusations? Yours, Rehan.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: the second group in a double-booked hall. Remedy: comparable new slot, priority, and no extra fee.",
          "prompt": "Write to the hall manager confirming what you need.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the affected group's viewpoint.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "remedy",
              "description": "Includes supplied remedy terms.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "request",
              "description": "Asks for relevant confirmation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the affected group's viewpoint.",
              "any_of": [
                "our group",
                "we"
              ]
            },
            {
              "id": "remedy",
              "description": "Includes supplied remedy terms.",
              "any_of": [
                "comparable slot",
                "priority",
                "no extra fee"
              ]
            },
            {
              "id": "request",
              "description": "Asks for relevant confirmation.",
              "any_of": [
                "confirm",
                "date",
                "notice"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear",
                "Sincerely"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "our group",
            "we",
            "comparable slot",
            "priority",
            "no extra fee",
            "confirm",
            "date",
            "notice"
          ],
          "model_answer": "Dear Hall Manager, Our group accepts a comparable new slot because the system created the duplicate booking. Please confirm the priority date and that no extra fee will be charged. We also need enough notice to inform our members. Sincerely, Amina.",
          "pass_score": 0.8
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: caretaker reporting a shared-pipe leak. Evidence: plumber found the leak before the branches to homes.",
          "prompt": "Write a factual first-person update to residents.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the caretaker's reporting role.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Reports the shared-pipe finding accurately.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "States a bounded follow-up.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the caretaker's reporting role.",
              "any_of": [
                "I am writing",
                "I will share"
              ]
            },
            {
              "id": "evidence",
              "description": "Reports the shared-pipe finding accurately.",
              "any_of": [
                "shared pipe",
                "before branches",
                "no household blamed"
              ]
            },
            {
              "id": "next",
              "description": "States a bounded follow-up.",
              "any_of": [
                "repair",
                "next meter reading"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear Residents",
                "Regards"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "I am writing",
            "I will share",
            "shared pipe",
            "before branches",
            "no household blamed",
            "repair",
            "next meter reading",
            "Dear Residents"
          ],
          "model_answer": "Dear Residents, I am writing to report that the plumber found a leak in the shared pipe before it branches to any house. The repair team will fix that section first, so no household is being blamed. I will share the next meter reading after repair. Regards, Caretaker.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: younger brother accepting a written land division. Need: mark the boundary with both brothers present.",
          "prompt": "Write a first-person letter confirming acceptance and next step.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the younger brother's viewpoint.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Confirms the written division.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "Requests joint boundary marking.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the younger brother's viewpoint.",
              "any_of": [
                "I accept",
                "both of us"
              ]
            },
            {
              "id": "decision",
              "description": "Confirms the written division.",
              "any_of": [
                "division written",
                "accept"
              ]
            },
            {
              "id": "next",
              "description": "Requests joint boundary marking.",
              "any_of": [
                "surveyor",
                "boundary marked",
                "suitable day"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear",
                "Yours"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "I accept",
            "both of us",
            "division written",
            "accept",
            "surveyor",
            "boundary marked",
            "suitable day",
            "Dear"
          ],
          "model_answer": "Dear Elder Brother, I accept the division written in the document. Let us meet with the surveyor so the boundary is marked while both of us are present. Please suggest a suitable day. Yours, Mohan.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: library borrower whose fine was cancelled after the book was found behind larger books.",
          "prompt": "Write a courteous response that also suggests prevention.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the borrower's viewpoint.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Mentions record and found book.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "suggestion",
              "description": "Offers a relevant prevention idea.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the borrower's viewpoint.",
              "any_of": [
                "Thank you",
                "I appreciate"
              ]
            },
            {
              "id": "evidence",
              "description": "Mentions record and found book.",
              "any_of": [
                "return record",
                "behind larger volumes"
              ]
            },
            {
              "id": "suggestion",
              "description": "Offers a relevant prevention idea.",
              "any_of": [
                "labelled trolley",
                "until shelved"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear Librarian",
                "Sincerely"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "Thank you",
            "I appreciate",
            "return record",
            "behind larger volumes",
            "labelled trolley",
            "until shelved",
            "Dear Librarian",
            "Sincerely"
          ],
          "model_answer": "Dear Librarian, Thank you for checking the return record and finding the book behind the larger volumes. I appreciate that the fine was cancelled. Could returned books be placed on a labelled trolley until they are shelved? Sincerely, Tara.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: captain after a disputed score was corrected by a transparent recount.",
          "prompt": "Write to the opposing captain acknowledging the process.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses one captain's first-person voice.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Names observers and stuck ballots.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "relationship",
              "description": "Acknowledges the other side respectfully.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses one captain's first-person voice.",
              "any_of": [
                "I accept",
                "I hope"
              ]
            },
            {
              "id": "evidence",
              "description": "Names observers and stuck ballots.",
              "any_of": [
                "observers",
                "recount",
                "stuck ballots"
              ]
            },
            {
              "id": "relationship",
              "description": "Acknowledges the other side respectfully.",
              "any_of": [
                "Thank you",
                "same process next time"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear Captain",
                "Regards"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "I accept",
            "I hope",
            "observers",
            "recount",
            "stuck ballots",
            "Thank you",
            "same process next time",
            "Dear Captain"
          ],
          "model_answer": "Dear Captain, I accept the corrected total because both observers watched the recount and the stuck ballots explained the error. Thank you for waiting until the evidence was checked. I hope we use the same process next time. Regards, Nila.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: resident affected by temporary bricks on a public path. Decision: safe route and removal deadline.",
          "prompt": "Write a letter checking that the decision will be implemented.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the affected resident's viewpoint.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Acknowledges temporary repair.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "request",
              "description": "Checks route and deadline.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the affected resident's viewpoint.",
              "any_of": [
                "I understand",
                "older residents"
              ]
            },
            {
              "id": "decision",
              "description": "Acknowledges temporary repair.",
              "any_of": [
                "two-day repair",
                "bricks"
              ]
            },
            {
              "id": "request",
              "description": "Checks route and deadline.",
              "any_of": [
                "safe route",
                "date removed"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear",
                "Yours sincerely"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "I understand",
            "older residents",
            "two-day repair",
            "bricks",
            "safe route",
            "date removed",
            "Dear",
            "Yours sincerely"
          ],
          "model_answer": "Dear Council Secretary, I understand that the bricks are needed for a two-day repair. Please confirm where the temporary safe route begins and the date by which the bricks will be removed. This will help older residents plan their walk. Yours sincerely, Farida.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "A first-person decision letter names the writer's role, responds to the actual decision and evidence, states an effect or feeling, asks for a relevant next step, and uses a greeting and closing.",
          "prompt": "State the letter checklist in your own words.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "role",
              "description": "Keeps the first-person role.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "content",
              "description": "Includes decision, evidence, and effect.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "Asks a useful next step.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Includes greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "role",
              "description": "Keeps the first-person role.",
              "any_of": [
                "affected person",
                "first person"
              ]
            },
            {
              "id": "content",
              "description": "Includes decision, evidence, and effect.",
              "any_of": [
                "decision",
                "evidence",
                "effect"
              ]
            },
            {
              "id": "next",
              "description": "Asks a useful next step.",
              "any_of": [
                "request",
                "next step"
              ]
            },
            {
              "id": "form",
              "description": "Includes greeting and closing.",
              "any_of": [
                "greeting",
                "closing"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "affected person",
            "first person",
            "decision",
            "evidence",
            "effect",
            "request",
            "next step",
            "greeting"
          ],
          "model_answer": "Write as the affected person, refer accurately to the decision and evidence, explain its effect, request a useful next step, and include a clear greeting and closing.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-first-person-letter-misconception",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "misconception": "The learner slips into third-person narration, invents new evidence, copies only the verdict, or omits reader, next step, greeting, or closing.",
          "remediation": "Use a role card and five-box letter plan: greeting, decision/evidence, effect, next request, closing; verify every factual claim against the source.",
          "support_check_ids": [
            "panchayat-first-person-letter-bridge",
            "panchayat-first-person-letter-masterclass",
            "panchayat-first-person-letter-revision1",
            "panchayat-first-person-letter-revision2",
            "panchayat-first-person-letter-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: the farmer whose seedlings were damaged. Decision: the player will replace them and the boundary will move.",
          "prompt": "Write a first-person letter to the council responding to the decision.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the farmer's first-person viewpoint.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Responds to both parts of the decision.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "request",
              "description": "Adds a relevant next question.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the farmer's first-person viewpoint.",
              "any_of": [
                "I accept",
                "my loss",
                "garden"
              ]
            },
            {
              "id": "decision",
              "description": "Responds to both parts of the decision.",
              "any_of": [
                "seedlings replaced",
                "boundary moved"
              ]
            },
            {
              "id": "request",
              "description": "Adds a relevant next question.",
              "any_of": [
                "when",
                "boundary marked"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear",
                "Yours sincerely"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "I accept",
            "my loss",
            "garden",
            "seedlings replaced",
            "boundary moved",
            "when",
            "boundary marked",
            "Dear"
          ],
          "model_answer": "Dear Council Members, I accept the decision that the damaged seedlings will be replaced and the play boundary moved. This repairs my loss and should prevent another ball from reaching the garden. Please tell me when the new boundary will be marked. Yours sincerely, Hari.",
          "pass_score": 0.8
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: a student wrongly blamed for a torn net. Evidence: the log showed the tear existed before school.",
          "prompt": "Write a short letter to the sports teacher after the finding.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the student's first-person experience.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Mentions the earlier log.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "Suggests a relevant improvement.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the student's first-person experience.",
              "any_of": [
                "my team",
                "I felt",
                "we were blamed"
              ]
            },
            {
              "id": "evidence",
              "description": "Mentions the earlier log.",
              "any_of": [
                "equipment log",
                "earlier record"
              ]
            },
            {
              "id": "next",
              "description": "Suggests a relevant improvement.",
              "any_of": [
                "check the log",
                "future"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear",
                "Yours"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "my team",
            "I felt",
            "we were blamed",
            "equipment log",
            "earlier record",
            "check the log",
            "future",
            "Dear"
          ],
          "model_answer": "Dear Ma'am, Thank you for checking the equipment log and clearing my team. I felt worried when we were blamed, but the earlier record showed what happened. Could the class check the log before future accusations? Yours, Rehan.",
          "pass_score": 0.8
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: the second group in a double-booked hall. Remedy: comparable new slot, priority, and no extra fee.",
          "prompt": "Write to the hall manager confirming what you need.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the affected group's viewpoint.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "remedy",
              "description": "Includes supplied remedy terms.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "request",
              "description": "Asks for relevant confirmation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the affected group's viewpoint.",
              "any_of": [
                "our group",
                "we"
              ]
            },
            {
              "id": "remedy",
              "description": "Includes supplied remedy terms.",
              "any_of": [
                "comparable slot",
                "priority",
                "no extra fee"
              ]
            },
            {
              "id": "request",
              "description": "Asks for relevant confirmation.",
              "any_of": [
                "confirm",
                "date",
                "notice"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear",
                "Sincerely"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "our group",
            "we",
            "comparable slot",
            "priority",
            "no extra fee",
            "confirm",
            "date",
            "notice"
          ],
          "model_answer": "Dear Hall Manager, Our group accepts a comparable new slot because the system created the duplicate booking. Please confirm the priority date and that no extra fee will be charged. We also need enough notice to inform our members. Sincerely, Amina.",
          "pass_score": 0.8
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: caretaker reporting a shared-pipe leak. Evidence: plumber found the leak before the branches to homes.",
          "prompt": "Write a factual first-person update to residents.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the caretaker's reporting role.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "evidence",
              "description": "Reports the shared-pipe finding accurately.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "States a bounded follow-up.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the caretaker's reporting role.",
              "any_of": [
                "I am writing",
                "I will share"
              ]
            },
            {
              "id": "evidence",
              "description": "Reports the shared-pipe finding accurately.",
              "any_of": [
                "shared pipe",
                "before branches",
                "no household blamed"
              ]
            },
            {
              "id": "next",
              "description": "States a bounded follow-up.",
              "any_of": [
                "repair",
                "next meter reading"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear Residents",
                "Regards"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "I am writing",
            "I will share",
            "shared pipe",
            "before branches",
            "no household blamed",
            "repair",
            "next meter reading",
            "Dear Residents"
          ],
          "model_answer": "Dear Residents, I am writing to report that the plumber found a leak in the shared pipe before it branches to any house. The repair team will fix that section first, so no household is being blamed. I will share the next meter reading after repair. Regards, Caretaker.",
          "pass_score": 0.8
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "panchayat-first-person-letter-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Stay inside the assigned role, refer to the actual decision, explain its effect, request one useful next step, and check letter punctuation.",
          "passage": "Role: younger brother accepting a written land division. Need: mark the boundary with both brothers present.",
          "prompt": "Write a first-person letter confirming acceptance and next step.",
          "skill_ids": [
            "grammar.punctuation_capitalization",
            "writing.friendly_message",
            "writing.paragraph"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "voice",
              "description": "Uses the younger brother's viewpoint.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "decision",
              "description": "Confirms the written division.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "next",
              "description": "Requests joint boundary marking.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "voice",
              "description": "Uses the younger brother's viewpoint.",
              "any_of": [
                "I accept",
                "both of us"
              ]
            },
            {
              "id": "decision",
              "description": "Confirms the written division.",
              "any_of": [
                "division written",
                "accept"
              ]
            },
            {
              "id": "next",
              "description": "Requests joint boundary marking.",
              "any_of": [
                "surveyor",
                "boundary marked",
                "suitable day"
              ]
            },
            {
              "id": "form",
              "description": "Uses greeting and closing.",
              "any_of": [
                "Dear",
                "Yours"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "I accept",
            "both of us",
            "division written",
            "accept",
            "surveyor",
            "boundary marked",
            "suitable day",
            "Dear"
          ],
          "model_answer": "Dear Elder Brother, I accept the division written in the document. Let us meet with the surveyor so the boundary is marked while both of us are present. Please suggest a suitable day. Yours, Mohan.",
          "pass_score": 0.8
        }
      }
    },
    {
      "level_id": "panchayat-less-words",
      "title": "Build -less Words That Actually Exist",
      "focus": "form and verify words meaning without a quality or thing",
      "outcome": "Add -less where it creates an established word, explain the resulting 'without' meaning in context, and reject invented or misleading forms.",
      "skill_ids": [
        "vocab.word_formation",
        "vocab.chapter_word_usage"
      ],
      "episode_kind": "meaning_encounter",
      "source_anchor_ids": [
        "eng_c5_ch08:language:6-8"
      ],
      "connect": {
        "teaching_block": "The suffix -less often means 'without', as in endless or leafless. It cannot attach naturally to every noun, and a built word may have limits that context must preserve.",
        "passage": "Leafless means without leaves, but it does not prove a tree is dead. Fairless is not the usual opposite of fair; English uses unfair.",
        "prompt": "Check both meaning and whether the form is a real word, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-less-words-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
        "passage": "A rule with no fairness is a ____ rule.",
        "prompt": "Build the -less word and explain its meaning.",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "options": [
          "fairless means fair",
          "unfair; 'fairless' is not the taught standard word",
          "refair means no fairness",
          "fairly replaces the noun"
        ],
        "accepted_answers": [
          "unfair; 'fairless' is not the taught standard word"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "panchayat-less-words-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A path with no end in sight can be described as endless.",
          "prompt": "How does -less change 'end'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "ending again",
            "full of endings",
            "before the end",
            "without an end"
          ],
          "accepted_answers": [
            "without an end"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "panchayat-less-words-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A child who feels no fear in a difficult moment may be called fearless.",
          "prompt": "Explain the built word without claiming the child takes unsafe risks.",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "full of fear",
            "fear again",
            "unable to feel anything",
            "without fear, not without safety"
          ],
          "accepted_answers": [
            "without fear, not without safety"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-less-words-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A bottle with no water is waterless.",
          "prompt": "Choose the sentence that uses waterless accurately.",
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
                "waterless",
                "without water",
                "dry"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "waterless",
            "without water",
            "dry"
          ],
          "model_answer": "The dry camp had a waterless storage drum awaiting the tanker.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-less-words-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A statement with no care may be careless.",
          "prompt": "Distinguish careless from care-free in this context.",
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
                "careless",
                "not enough care",
                "not relaxed"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "careless",
            "not enough care",
            "not relaxed"
          ],
          "model_answer": "'Careless' means not taking enough care; it does not simply mean relaxed and free from worry.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-less-words-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A night without stars may be described as starless.",
          "prompt": "Use starless in an original complete sentence.",
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
                "starless",
                "without visible stars",
                "night"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "starless",
            "without visible stars",
            "night"
          ],
          "model_answer": "Clouds covered the sky, leaving the village under a starless night.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-less-words-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A room with no sound can be called soundless, though 'silent' is more common.",
          "prompt": "Explain the meaning and one natural alternative.",
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
                "soundless",
                "without sound",
                "silent"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "soundless",
            "without sound",
            "silent"
          ],
          "model_answer": "'Soundless' means without sound, and 'silent' is a natural alternative in many sentences.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-less-words-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A journey with no trouble is sometimes called trouble-free; 'troubleless' is uncommon.",
          "prompt": "What should a careful word builder do?",
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
                "verify word",
                "established",
                "not every noun"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "verify word",
            "established",
            "not every noun"
          ],
          "model_answer": "A careful writer should verify that the built form is an established word instead of assuming -less can attach to every noun.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-less-words-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "The suffix -less usually means 'without', but the resulting form must be a real word whose meaning fits the sentence.",
          "prompt": "State the word-formation test.",
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
                "base",
                "without",
                "verify",
                "context"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "base",
            "without",
            "verify",
            "context"
          ],
          "model_answer": "Define the base, apply 'without', verify the built word, and test it in context.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-less-words-misconception",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "misconception": "The learner attaches -less mechanically to any base or extends 'without X' into an unsupported judgement.",
          "remediation": "Use a four-step word test: base meaning, 'without' meaning, dictionary/known-form check, and sentence-limit check.",
          "support_check_ids": [
            "panchayat-less-words-bridge",
            "panchayat-less-words-masterclass",
            "panchayat-less-words-revision1",
            "panchayat-less-words-revision2",
            "panchayat-less-words-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "panchayat-less-words-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A rule with no fairness is a ____ rule.",
          "prompt": "Build the -less word and explain its meaning.",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "fairless means fair",
            "refair means no fairness",
            "unfair; 'fairless' is not the taught standard word",
            "fairly replaces the noun"
          ],
          "accepted_answers": [
            "unfair; 'fairless' is not the taught standard word"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "panchayat-less-words-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A path with no end in sight can be described as endless.",
          "prompt": "How does -less change 'end'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "ending again",
            "full of endings",
            "before the end",
            "without an end"
          ],
          "accepted_answers": [
            "without an end"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "panchayat-less-words-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A child who feels no fear in a difficult moment may be called fearless.",
          "prompt": "Explain the built word without claiming the child takes unsafe risks.",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "without fear, not without safety",
            "full of fear",
            "fear again",
            "unable to feel anything"
          ],
          "accepted_answers": [
            "without fear, not without safety"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "panchayat-less-words-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A bottle with no water is waterless.",
          "prompt": "Choose the sentence that uses waterless accurately.",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "the waterless river overflowed",
            "waterless means filled twice",
            "the drum was without water",
            "waterless names a young animal"
          ],
          "accepted_answers": [
            "the drum was without water"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "panchayat-less-words-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Define the base, apply 'without', verify that the built form is established, and test what the sentence does and does not imply.",
          "passage": "A statement with no care may be careless.",
          "prompt": "Distinguish careless from care-free in this context.",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "not taking enough care",
            "taking extra care",
            "feeling relaxed",
            "caring again"
          ],
          "accepted_answers": [
            "not taking enough care"
          ]
        }
      }
    },
    {
      "level_id": "panchayat-bounded-research",
      "title": "Report What the Source Actually Says",
      "focus": "select and paraphrase relevant profile and transfer facts",
      "outcome": "Select relevant facts from a bounded source card, preserve quantities and conditions, paraphrase accurately, and state when a stronger conclusion is unsupported.",
      "skill_ids": [
        "research.information_selection"
      ],
      "episode_kind": "application_mission",
      "source_anchor_ids": [
        "eng_c5_ch08:transfer:11-14"
      ],
      "connect": {
        "teaching_block": "A facilitator may also read profile cards aloud. Here, select facts from the visible source and keep the report accurate, relevant, and honest about what the source does not establish.",
        "passage": "Card: The club meets on Friday and publishes interviews only after consent review. Supported report: Friday meetings; consent comes before publication.",
        "prompt": "Separate the supported facts from unstated claims, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "panchayat-bounded-research-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
        "passage": "Profile card: Savita Rao founded a mobile library in 2012. It visits six villages every fortnight and lends books free of charge.",
        "prompt": "Select two facts that explain the service and report them accurately.",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "six villages; free fortnightly lending",
          "she founded six schools",
          "it visits every village daily",
          "the card states a membership fee"
        ],
        "accepted_answers": [
          "six villages; free fortnightly lending"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "panchayat-bounded-research-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Abdul Karim repairs hand pumps. He trained twenty local volunteers to identify loose handles and leaking seals, but only trained mechanics replace internal parts.",
          "prompt": "Report the volunteer role and its safety boundary.",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "volunteers inspect; mechanics replace internal parts",
            "volunteers rebuild every pump",
            "mechanics only write reports",
            "the card permits children to repair parts"
          ],
          "accepted_answers": [
            "volunteers inspect; mechanics replace internal parts"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "panchayat-bounded-research-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Meena Das won a district storytelling award in 2024 for retelling local folktales in English and Bengali.",
          "prompt": "Which statement is fully supported?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "national award for writing novels",
            "district award for bilingual folktale retelling",
            "award in 2014",
            "stories only in Hindi"
          ],
          "accepted_answers": [
            "district award for bilingual folktale retelling"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-bounded-research-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Dr. Lhamo studies mountain insects. Her team photographs species, records altitude, and releases each insect after observation.",
          "prompt": "Summarise the research procedure without adding a capture claim.",
          "skill_ids": [
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
                "photographs",
                "records altitude",
                "releases"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "photographs",
            "records altitude",
            "releases"
          ],
          "model_answer": "The team photographs insects, records where they were found by altitude, and releases them after observation.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-bounded-research-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Rakesh Menon designed low-cost ramps for three public buildings after interviewing wheelchair users about difficult entrances.",
          "prompt": "Explain how evidence shaped the design.",
          "skill_ids": [
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
                "interviews",
                "entrance difficulties",
                "ramps",
                "three buildings"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "interviews",
            "entrance difficulties",
            "ramps",
            "three buildings"
          ],
          "model_answer": "Interviews with wheelchair users identified entrance difficulties, and those findings informed low-cost ramps in three buildings.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-bounded-research-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Noor's seed bank stores labelled local seeds in dry jars. Farmers record crop, village, and collection year before depositing seeds.",
          "prompt": "Select the required record fields and storage method.",
          "skill_ids": [
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
                "labelled dry jars",
                "crop",
                "village",
                "year"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "labelled dry jars",
            "crop",
            "village",
            "year"
          ],
          "model_answer": "Seeds are stored in labelled dry jars, and each deposit records crop, village, and collection year.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-bounded-research-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Coach Anita schedules mixed-age practice. Older players demonstrate one drill, younger players attempt it, and feedback follows before the next drill.",
          "prompt": "Report the teaching sequence.",
          "skill_ids": [
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
                "demonstrate",
                "attempt",
                "feedback",
                "next drill"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "demonstrate",
            "attempt",
            "feedback",
            "next drill"
          ],
          "model_answer": "An older player demonstrates, younger players try the drill, and feedback comes before the group moves on.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "panchayat-bounded-research-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: The river-watch group tests clarity weekly at the same three points. The card gives no chemical-safety result.",
          "prompt": "Write a responsible summary with the missing-evidence boundary.",
          "skill_ids": [
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
                "weekly clarity",
                "three fixed points",
                "no chemical safety"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "weekly clarity",
            "three fixed points",
            "no chemical safety"
          ],
          "model_answer": "The group compares weekly clarity at three fixed points, but the card does not establish chemical safety.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "panchayat-bounded-research-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "A bounded profile answer selects relevant supplied facts, reports them in its own sentence, preserves numbers and conditions, and states when the source does not support a stronger claim.",
          "prompt": "State the research-selection checklist.",
          "skill_ids": [
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
                "relevant facts",
                "numbers and limits",
                "paraphrase",
                "unknown"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "relevant facts",
            "numbers and limits",
            "paraphrase",
            "unknown"
          ],
          "model_answer": "Choose relevant facts, preserve their numbers and limits, paraphrase accurately, and mark unsupported conclusions as unknown.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "panchayat-bounded-research-misconception",
          "skill_ids": [
            "research.information_selection"
          ],
          "misconception": "The learner copies every detail, changes quantities, merges separate facts, or invents an impressive conclusion not supported by the card.",
          "remediation": "Use answer-needed, exact fact, paraphrase, and evidence-limit columns; compare the final sentence back to every source number and condition.",
          "support_check_ids": [
            "panchayat-bounded-research-bridge",
            "panchayat-bounded-research-masterclass",
            "panchayat-bounded-research-revision1",
            "panchayat-bounded-research-revision2",
            "panchayat-bounded-research-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "panchayat-bounded-research-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Savita Rao founded a mobile library in 2012. It visits six villages every fortnight and lends books free of charge.",
          "prompt": "Select two facts that explain the service and report them accurately.",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "she founded six schools",
            "six villages; free fortnightly lending",
            "it visits every village daily",
            "the card states a membership fee"
          ],
          "accepted_answers": [
            "six villages; free fortnightly lending"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "panchayat-bounded-research-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Abdul Karim repairs hand pumps. He trained twenty local volunteers to identify loose handles and leaking seals, but only trained mechanics replace internal parts.",
          "prompt": "Report the volunteer role and its safety boundary.",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "volunteers rebuild every pump",
            "volunteers inspect; mechanics replace internal parts",
            "mechanics only write reports",
            "the card permits children to repair parts"
          ],
          "accepted_answers": [
            "volunteers inspect; mechanics replace internal parts"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "panchayat-bounded-research-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Meena Das won a district storytelling award in 2024 for retelling local folktales in English and Bengali.",
          "prompt": "Which statement is fully supported?",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "national award for writing novels",
            "award in 2014",
            "stories only in Hindi",
            "district award for bilingual folktale retelling"
          ],
          "accepted_answers": [
            "district award for bilingual folktale retelling"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "panchayat-bounded-research-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Dr. Lhamo studies mountain insects. Her team photographs species, records altitude, and releases each insect after observation.",
          "prompt": "Summarise the research procedure without adding a capture claim.",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "keeps every insect permanently",
            "photograph, record altitude, release",
            "studies only mountain plants",
            "the card says insects are harmed"
          ],
          "accepted_answers": [
            "photograph, record altitude, release"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "panchayat-bounded-research-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Highlight the facts that answer the question, preserve numbers and limits, and mark missing evidence instead of filling it with a guess.",
          "passage": "Profile card: Rakesh Menon designed low-cost ramps for three public buildings after interviewing wheelchair users about difficult entrances.",
          "prompt": "Explain how evidence shaped the design.",
          "skill_ids": [
            "research.information_selection"
          ],
          "options": [
            "user interviews informed ramp design",
            "ramps were designed before any evidence",
            "he built three wheelchairs",
            "the card says ramps were expensive"
          ],
          "accepted_answers": [
            "user interviews informed ramp design"
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
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-sequence-summary-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A library book is marked missing. The desk record shows it was returned, a shelf check finds it behind larger books, and the borrower's fine is cancelled.",
        "prompt": "Transfer the event-sequence strategy: what evidence leads to the final action?",
        "skill_ids": [
          "reading.event_sequence",
          "writing.summary_own_words"
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
              "return record",
              "shelf search",
              "book found",
              "fine cancelled"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "return record",
          "shelf search",
          "book found",
          "fine cancelled"
        ],
        "model_answer": "The return record triggers a shelf search, the book is found, and the unsupported fine is cancelled.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-sequence-summary-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A clinic queue dispute begins when two tokens show the same number. Staff compare issue times, discover a printer jam caused the duplicate, and call patients in the original time order.",
        "prompt": "Write the ordered reasoning that restores the queue.",
        "skill_ids": [
          "reading.event_sequence",
          "writing.summary_own_words"
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
              "compare times",
              "printer jam",
              "original order",
              "fair queue"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "compare times",
          "printer jam",
          "original order",
          "fair queue"
        ],
        "model_answer": "Staff compare issue times, identify the printer jam, and use the original time order to call patients fairly.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-sequence-summary-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A science model breaks during display. Three students blame one another. A nearby camera shows the table leg collapsed without anyone touching it, so the group repairs the leg and shares the rebuilding work.",
        "prompt": "Which sequence separates claim, evidence, and response?",
        "skill_ids": [
          "reading.event_sequence",
          "writing.summary_own_words"
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
              "accusations",
              "recording evidence",
              "table failure",
              "repair together"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "accusations",
          "recording evidence",
          "table failure",
          "repair together"
        ],
        "model_answer": "Students make accusations, the recording shows a table failure, and the group responds by repairing the leg and rebuilding together.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-sequence-summary-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A complete narrative summary includes the triggering conflict, the evidence or reasoning used, the decision, and its effect; it excludes colourful details that do not change the outcome.",
        "prompt": "State the four-part summary rule in your own words.",
        "skill_ids": [
          "reading.event_sequence",
          "writing.summary_own_words"
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
              "conflict",
              "evidence checked",
              "decision",
              "result"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "conflict",
          "evidence checked",
          "decision",
          "result"
        ],
        "model_answer": "Name the conflict, show how evidence was checked, state the decision, and explain the result while omitting irrelevant decoration.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-dialogue-attribution-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Coach: 'Why did you stop the drill?' Player: 'A child entered the throwing lane.'",
        "prompt": "Identify speaker, listener, and purpose of the second turn.",
        "skill_ids": [
          "reading.dialogue_attribution"
        ],
        "options": [
          "coach explains the safety stop to the player",
          "player explains the safety stop to coach",
          "player asks the coach to continue the drill",
          "child explains the lane rule to the coach"
        ],
        "accepted_answers": [
          "player explains the safety stop to coach"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-dialogue-attribution-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Librarian: 'This card belongs to shelf C.' Student: 'Then I placed it on the wrong trolley.'",
        "prompt": "What does 'Then' show in the student's turn?",
        "skill_ids": [
          "reading.dialogue_attribution"
        ],
        "options": [
          "the librarian recognises an error",
          "the student recognises an error",
          "the student confirms that the trolley was correct",
          "the student thinks shelf C has changed"
        ],
        "accepted_answers": [
          "the student recognises an error"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-dialogue-attribution-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Parent: 'The bus arrived late.' Driver: 'A fallen branch blocked the route for fifteen minutes.'",
        "prompt": "Which speaker supplies the cause?",
        "skill_ids": [
          "reading.dialogue_attribution"
        ],
        "options": [
          "the parent",
          "the driver",
          "the bus",
          "the fifteen minutes"
        ],
        "accepted_answers": [
          "the driver"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-dialogue-attribution-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Dialogue attribution requires three checks: who speaks, whom the turn addresses, and what the turn does, such as claim, question, evidence, agreement, challenge, or decision.",
        "prompt": "State the dialogue-tracking rule.",
        "skill_ids": [
          "reading.dialogue_attribution"
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
              "speaker",
              "listener",
              "turn function"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "speaker",
          "listener",
          "turn function"
        ],
        "model_answer": "Identify the speaker and listener, then name the function of the turn using only what is visibly said.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-fairness-reasoning-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A race winner stepped outside the marked lane to avoid a fallen runner, then returned immediately. The rules normally disqualify leaving the lane.",
        "prompt": "Apply the rule with attention to purpose and evidence.",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "verify",
            "description": "Checks the safety reason.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "purpose",
            "description": "Distinguishes safety from advantage.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "future",
            "description": "Records and clarifies.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "verify",
            "description": "Checks the safety reason.",
            "any_of": [
              "avoid fallen runner",
              "verify"
            ]
          },
          {
            "id": "purpose",
            "description": "Distinguishes safety from advantage.",
            "any_of": [
              "not gain advantage",
              "safety action"
            ]
          },
          {
            "id": "future",
            "description": "Records and clarifies.",
            "any_of": [
              "record incident",
              "emergency rule"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "avoid fallen runner",
          "verify",
          "not gain advantage",
          "safety action",
          "record incident",
          "emergency rule"
        ],
        "model_answer": "Verify that the lane exit was only to avoid the fallen runner. If confirmed, do not treat the safety action as gaining an advantage; record the incident and clarify the emergency rule.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-fairness-reasoning-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A parcel is delivered to the wrong house. The resident opens only the outer label, notices the name mismatch, and calls the courier without opening the package.",
        "prompt": "Evaluate the response and state the next fair action.",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "privacy",
            "description": "Recognises the protected action.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "action",
            "description": "Uses the delivery process.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "privacy",
            "description": "Recognises the protected action.",
            "any_of": [
              "not opening package",
              "privacy"
            ]
          },
          {
            "id": "action",
            "description": "Uses the delivery process.",
            "any_of": [
              "call courier",
              "return",
              "label record"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 12,
        "relevance_terms": [
          "not opening package",
          "privacy",
          "call courier",
          "return",
          "label record"
        ],
        "model_answer": "The resident protects privacy by not opening the package and should return it through the courier using the correct label record.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-fairness-reasoning-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A community hall booking was entered twice for the same evening. Both groups have confirmation messages sent one minute apart; the hall manager's system created the duplicate.",
        "prompt": "Propose a fair remedy that does not blame either group.",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "cause",
            "description": "Assigns the error correctly.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "order",
            "description": "Uses the recorded times.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "remedy",
            "description": "Provides a meaningful alternative.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "cause",
            "description": "Assigns the error correctly.",
            "any_of": [
              "system error",
              "not groups"
            ]
          },
          {
            "id": "order",
            "description": "Uses the recorded times.",
            "any_of": [
              "earlier confirmation",
              "first group"
            ]
          },
          {
            "id": "remedy",
            "description": "Provides a meaningful alternative.",
            "any_of": [
              "comparable alternative",
              "priority",
              "no extra fee"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "system error",
          "not groups",
          "earlier confirmation",
          "first group",
          "comparable alternative",
          "priority",
          "no extra fee"
        ],
        "model_answer": "Acknowledge the system error, offer the earlier confirmed slot to the first group, and give the second group a comparable alternative with priority and no extra fee.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-fairness-reasoning-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Fair decisions hear affected sides, identify the actual claim, test relevant evidence, explain the rule or principle, choose a proportionate remedy, and record any uncertainty.",
        "prompt": "State the fairness checklist in your own words.",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "hearing",
            "description": "Includes affected sides and claim.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "evidence",
            "description": "Checks relevant evidence.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "principle",
            "description": "States the rule used.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "remedy",
            "description": "Keeps remedy proportionate and uncertainty visible.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "hearing",
            "description": "Includes affected sides and claim.",
            "any_of": [
              "hear affected",
              "clarify claim"
            ]
          },
          {
            "id": "evidence",
            "description": "Checks relevant evidence.",
            "any_of": [
              "verify evidence"
            ]
          },
          {
            "id": "principle",
            "description": "States the rule used.",
            "any_of": [
              "apply principle"
            ]
          },
          {
            "id": "remedy",
            "description": "Keeps remedy proportionate and uncertainty visible.",
            "any_of": [
              "fits harm",
              "uncertainty"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 24,
        "relevance_terms": [
          "hear affected",
          "clarify claim",
          "verify evidence",
          "apply principle",
          "fits harm",
          "uncertainty"
        ],
        "model_answer": "Hear the people affected, clarify the claim, verify relevant evidence, apply a stated principle, choose a remedy that fits the harm, and disclose uncertainty.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-language-relations-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The ball rolled ___ the bench and stopped ___ two bags.",
        "prompt": "Transfer the preposition strategy to a new setting.",
        "skill_ids": [
          "reading.word_meaning_context",
          "grammar.prepositions"
        ],
        "options": [
          "during; from",
          "with; to",
          "among; through",
          "under; between"
        ],
        "accepted_answers": [
          "under; between"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-language-relations-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The train travelled ___ the tunnel and arrived ___ the platform at noon.",
        "prompt": "Choose prepositions for movement and destination.",
        "skill_ids": [
          "reading.word_meaning_context",
          "grammar.prepositions"
        ],
        "options": [
          "under; between",
          "among; during",
          "through; at",
          "with; from"
        ],
        "accepted_answers": [
          "through; at"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-language-relations-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "'Reconcile' means to restore agreement or make two accounts consistent after a disagreement.",
        "prompt": "Choose the sentence that fits this meaning.",
        "skill_ids": [
          "reading.word_meaning_context",
          "grammar.prepositions"
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
              "reconcile",
              "make consistent",
              "correct entry"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "reconcile",
          "make consistent",
          "correct entry"
        ],
        "model_answer": "The treasurer reconciled the two lists by finding and correcting the missing entry.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-language-relations-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Prepositions express relationships such as place, movement, time, and connection. Vocabulary meaning comes from definition clues, actions, contrasts, and results around the word.",
        "prompt": "State the two-part language strategy.",
        "skill_ids": [
          "reading.word_meaning_context",
          "grammar.prepositions"
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
              "name relationship",
              "surrounding clues",
              "whole sentence"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "name relationship",
          "surrounding clues",
          "whole sentence"
        ],
        "model_answer": "Name the relationship before choosing a preposition, and use surrounding clues to test a vocabulary meaning in the whole sentence.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-past-chronology-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "By noon, the mechanic had repaired the pump, and residents collected water in the afternoon.",
        "prompt": "Transfer the tense reasoning to this service event.",
        "skill_ids": [
          "grammar.tense_usage"
        ],
        "options": [
          "collection happened before the repair",
          "both actions happened at noon",
          "repair and collection happened at the same time",
          "repair first, collection later"
        ],
        "accepted_answers": [
          "repair first, collection later"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-past-chronology-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The librarian had placed the returned book on the trolley before the shelf check began.",
        "prompt": "Which phrase marks the earlier completed action?",
        "skill_ids": [
          "grammar.tense_usage"
        ],
        "options": [
          "had placed",
          "began",
          "returned book",
          "on the trolley"
        ],
        "accepted_answers": [
          "had placed"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-past-chronology-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "After the chef had measured the flour, she mixed the dough.",
        "prompt": "Use past perfect and simple past to explain the sequence.",
        "skill_ids": [
          "grammar.tense_usage"
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
              "had measured",
              "mixed later"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "had measured",
          "mixed later"
        ],
        "model_answer": "The chef had measured the flour first, and then she mixed the dough.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-past-chronology-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Past perfect uses had plus a past participle to mark an earlier past action when another past action provides the reference point.",
        "prompt": "State the form-and-purpose rule.",
        "skill_ids": [
          "grammar.tense_usage"
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
              "had",
              "past participle",
              "earlier event",
              "simple past later"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "had",
          "past participle",
          "earlier event",
          "simple past later"
        ],
        "model_answer": "Use had plus the past participle for the earlier completed event, and use simple past for the later reference event.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-clue-prediction-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Text-card clues: the train platform display changes to 'delayed 20 minutes', and passengers move back from the edge.",
        "prompt": "Transfer the clue strategy to travel.",
        "skill_ids": [
          "reading.paragraph_main_idea",
          "writing.short_answer"
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
              "delay 20 minutes",
              "passengers wait",
              "stand back"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "delay 20 minutes",
          "passengers wait",
          "stand back"
        ],
        "model_answer": "Passengers will likely wait longer and stand back because the display reports a twenty-minute delay.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-clue-prediction-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Clues: half the cake remains, plates are stacked, and guests are putting on shoes.",
        "prompt": "What stage of the gathering is most likely?",
        "skill_ids": [
          "reading.paragraph_main_idea",
          "writing.short_answer"
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
              "gathering ending",
              "plates stacked",
              "guests shoes"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "gathering ending",
          "plates stacked",
          "guests shoes"
        ],
        "model_answer": "The gathering is probably ending because food remains but plates are stacked and guests are preparing to leave.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-clue-prediction-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Clues: a notebook page has three crossed-out totals, a calculator is open, and the final total is circled.",
        "prompt": "Infer the process that probably occurred.",
        "skill_ids": [
          "reading.paragraph_main_idea",
          "writing.short_answer"
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
              "recalculated",
              "crossed totals",
              "circled result"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "recalculated",
          "crossed totals",
          "circled result"
        ],
        "model_answer": "Someone likely recalculated the total several times and circled the corrected result.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-first-person-letter-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Role: patient with duplicate queue token. Resolution: original issue time restores order.",
        "prompt": "Transfer the first-person letter structure to the clinic.",
        "skill_ids": [
          "grammar.punctuation_capitalization",
          "writing.friendly_message",
          "writing.paragraph"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "voice",
            "description": "Uses the patient's viewpoint.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "resolution",
            "description": "Mentions jam, time, and restored order.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "request",
            "description": "Asks a relevant next step.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "form",
            "description": "Uses greeting and closing.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "voice",
            "description": "Uses the patient's viewpoint.",
            "any_of": [
              "my duplicate token",
              "I understand"
            ]
          },
          {
            "id": "resolution",
            "description": "Mentions jam, time, and restored order.",
            "any_of": [
              "printer jam",
              "issue time",
              "original order"
            ]
          },
          {
            "id": "request",
            "description": "Asks a relevant next step.",
            "any_of": [
              "where to wait"
            ]
          },
          {
            "id": "form",
            "description": "Uses greeting and closing.",
            "any_of": [
              "Dear",
              "Regards"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 24,
        "relevance_terms": [
          "my duplicate token",
          "I understand",
          "printer jam",
          "issue time",
          "original order",
          "where to wait",
          "Dear",
          "Regards"
        ],
        "model_answer": "Dear Reception Team, I understand that a printer jam created my duplicate token. Thank you for checking the issue time and restoring the original order. Please let me know where to wait while the queue is corrected. Regards, Sameer.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-first-person-letter-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Role: project member whose research contribution was recorded in the work log.",
        "prompt": "Write a respectful note about fair recognition.",
        "skill_ids": [
          "grammar.punctuation_capitalization",
          "writing.friendly_message",
          "writing.paragraph"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "voice",
            "description": "Uses the member's viewpoint without erasing others.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "evidence",
            "description": "Reports all documented roles.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "request",
            "description": "Asks for fair credit.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "form",
            "description": "Uses greeting and closing.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "voice",
            "description": "Uses the member's viewpoint without erasing others.",
            "any_of": [
              "I researched",
              "our shared result"
            ]
          },
          {
            "id": "evidence",
            "description": "Reports all documented roles.",
            "any_of": [
              "work log",
              "drew",
              "wrote",
              "presented"
            ]
          },
          {
            "id": "request",
            "description": "Asks for fair credit.",
            "any_of": [
              "credit each role"
            ]
          },
          {
            "id": "form",
            "description": "Uses greeting and closing.",
            "any_of": [
              "Dear Teacher",
              "Yours"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 24,
        "relevance_terms": [
          "I researched",
          "our shared result",
          "work log",
          "drew",
          "wrote",
          "presented",
          "credit each role",
          "Dear Teacher"
        ],
        "model_answer": "Dear Teacher, The work log shows that I researched the local-history facts while Arun drew the map, Leela wrote the captions, and Zoya presented. Could the final display credit each role? I am proud of our shared result. Yours, Imran.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-first-person-letter-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Role: runner who left the lane to avoid a fallen child. Process: safety reason is being verified.",
        "prompt": "Write a factual statement to the referee without assuming the decision.",
        "skill_ids": [
          "grammar.punctuation_capitalization",
          "writing.friendly_message",
          "writing.paragraph"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "voice",
            "description": "Uses the runner's first-person account.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "facts",
            "description": "States safety reason and no advantage claim.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "request",
            "description": "Requests evidence review without demanding outcome.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "form",
            "description": "Uses greeting and closing.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "voice",
            "description": "Uses the runner's first-person account.",
            "any_of": [
              "I stepped",
              "I returned"
            ]
          },
          {
            "id": "facts",
            "description": "States safety reason and no advantage claim.",
            "any_of": [
              "fallen child",
              "immediately",
              "did not move ahead"
            ]
          },
          {
            "id": "request",
            "description": "Requests evidence review without demanding outcome.",
            "any_of": [
              "check observer",
              "before deciding"
            ]
          },
          {
            "id": "form",
            "description": "Uses greeting and closing.",
            "any_of": [
              "Dear Referee",
              "Sincerely"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 24,
        "relevance_terms": [
          "I stepped",
          "I returned",
          "fallen child",
          "immediately",
          "did not move ahead",
          "check observer",
          "before deciding",
          "Dear Referee"
        ],
        "model_answer": "Dear Referee, I stepped outside the lane because a child had fallen in front of me. I returned immediately and did not move ahead of another runner. Please check the observer account before deciding. Sincerely, Kavya.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-less-words-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A wireless speaker works without a physical signal wire between the device and speaker.",
        "prompt": "Transfer the suffix meaning to technology.",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "options": [
          "full of wires",
          "without a connecting wire",
          "a broken speaker",
          "a wire used again"
        ],
        "accepted_answers": [
          "without a connecting wire"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-less-words-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A leafless tree has no leaves at that time; it is not necessarily dead.",
        "prompt": "Use context to avoid an unsupported inference.",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "options": [
          "without leaves, not necessarily dead",
          "dead in every case",
          "covered with leaves",
          "a tree without roots"
        ],
        "accepted_answers": [
          "without leaves, not necessarily dead"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-less-words-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A sleeveless jacket has no sleeves but still has a body and opening.",
        "prompt": "Which meaning is supported?",
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
              "sleeveless",
              "without sleeves",
              "jacket"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "sleeveless",
          "without sleeves",
          "jacket"
        ],
        "model_answer": "'Sleeveless' means designed without sleeves.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-bounded-research-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Transfer card: A food cooperative opens on Tuesdays and Saturdays. Members bring containers; the card does not state home delivery.",
        "prompt": "Report schedule and requirement without inventing a service.",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "open every day",
          "containers are supplied",
          "open Tue/Sat; bring containers; no delivery claim",
          "home delivery is guaranteed"
        ],
        "accepted_answers": [
          "open Tue/Sat; bring containers; no delivery claim"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch08-assessment-panchayat-bounded-research-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Transfer card: A weather station records temperature at 8 a.m. and 2 p.m. The monthly chart compares these two daily readings.",
        "prompt": "What comparison is supported?",
        "skill_ids": [
          "research.information_selection"
        ],
        "options": [
          "compare rainfall and wind",
          "predict every storm",
          "compare 8 a.m. and 2 p.m. temperatures",
          "record temperature every minute"
        ],
        "accepted_answers": [
          "compare 8 a.m. and 2 p.m. temperatures"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch08-assessment-panchayat-bounded-research-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Transfer card: A craft group uses fallen palm leaves, dries them for three days, and weaves small baskets. It does not cut live leaves.",
        "prompt": "Summarise material, preparation, product, and boundary.",
        "skill_ids": [
          "research.information_selection"
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
              "fallen leaves",
              "three days",
              "baskets",
              "not live leaves"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "fallen leaves",
          "three days",
          "baskets",
          "not live leaves"
        ],
        "model_answer": "The group dries fallen palm leaves for three days and weaves them into small baskets without cutting live leaves.",
        "pass_score": 0.8
      }
    ],
    "strands": [
      {
        "strand_id": "panchayat-sequence-summary",
        "skill_ids": [
          "reading.event_sequence",
          "writing.summary_own_words"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-sequence-summary"
        ]
      },
      {
        "strand_id": "panchayat-dialogue-attribution",
        "skill_ids": [
          "reading.dialogue_attribution"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-dialogue-attribution"
        ]
      },
      {
        "strand_id": "panchayat-fairness-reasoning",
        "skill_ids": [
          "reading.inference_reason",
          "writing.reason_answer"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-fairness-reasoning"
        ]
      },
      {
        "strand_id": "panchayat-language-relations",
        "skill_ids": [
          "reading.word_meaning_context",
          "grammar.prepositions"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-language-relations"
        ]
      },
      {
        "strand_id": "panchayat-past-chronology",
        "skill_ids": [
          "grammar.tense_usage"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-past-chronology"
        ]
      },
      {
        "strand_id": "panchayat-clue-prediction",
        "skill_ids": [
          "reading.paragraph_main_idea",
          "writing.short_answer"
        ],
        "minimum_items": 3,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-clue-prediction"
        ]
      },
      {
        "strand_id": "panchayat-first-person-letter",
        "skill_ids": [
          "grammar.punctuation_capitalization",
          "writing.friendly_message",
          "writing.paragraph"
        ],
        "minimum_items": 3,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-first-person-letter"
        ]
      },
      {
        "strand_id": "panchayat-less-words",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "minimum_items": 3,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-less-words"
        ]
      },
      {
        "strand_id": "panchayat-bounded-research",
        "skill_ids": [
          "research.information_selection"
        ],
        "minimum_items": 3,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "panchayat-bounded-research"
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
    "panchayat-sequence-summary": "Track the complaint, hearing, evidence, decision, and follow-up before compressing the complete change into a summary.",
    "panchayat-dialogue-attribution": "Use names, speech verbs, pronouns, and response links to identify who speaks, to whom, and for what purpose.",
    "panchayat-fairness-reasoning": "Judge the process from hearing, evidence, equal rules, reasons, and repair rather than a person's status.",
    "panchayat-language-relations": "Use position and relationship clues to interpret the key phrase, then place the correct relation word in a complete sentence.",
    "panchayat-past-chronology": "Use past forms and time signals to distinguish the earlier completed event from the later past event.",
    "panchayat-clue-prediction": "Predict only the next event supported by multiple clues and state the boundary on what remains unknown.",
    "panchayat-first-person-letter": "Write from the affected person's viewpoint with a clear event, feeling, request, reason, and respectful close.",
    "panchayat-less-words": "Check whether -less creates a real word meaning without the base noun, then verify that meaning in context.",
    "panchayat-bounded-research": "Report only attributed source facts, distinguish observation from inference, and state what the packet cannot prove.",
}


_DEPTH = {
    "panchayat-sequence-summary": {
        "guided": [
            _one(
                "Residents reported a broken streetlight. The clerk logged the location, an electrician inspected the pole, and the lamp was replaced the next morning.",
                "Retell the response in the correct order.",
                "The residents reported the fault, the clerk recorded it, the electrician inspected the pole, and the lamp was replaced.",
                "reported the fault, the clerk recorded it, the electrician inspected the pole, and the lamp was replaced",
                description="Preserves the complete response sequence.",
                skills=["reading.event_sequence"],
            ),
            _one(
                "Two families disputed a shared path. Both described their use, an old map was checked, and they agreed to mark a common walkway.",
                "State the main idea without repeating every detail.",
                "A path dispute was resolved through hearing both families, checking evidence, and agreeing on a shared walkway.",
                "dispute was resolved through hearing both families, checking evidence, and agreeing on a shared walkway",
                description="Summarises conflict, evidence, and resolution.",
                skills=["writing.summary_own_words"],
            ),
        ],
        "independent": [
            _two(
                "A shopkeeper complained that delivery carts blocked the lane each morning. The council heard drivers and residents, observed the lane at delivery time, and marked a loading space that must remain clear after nine o'clock. A review one week later found fewer blockages.",
                "Write a three-sentence summary that preserves the problem, process, and result.",
                "Morning delivery carts were blocking the lane. After hearing both groups and observing the site, the council marked a timed loading space. A later review found that the new arrangement reduced blockages.",
                ("process", "Includes complaint, hearing or observation, and decision.", "After hearing both groups and observing the site, the council marked a timed loading space"),
                ("result", "States the follow-up result.", "later review found that the new arrangement reduced blockages"),
                skills=["reading.event_sequence", "writing.summary_own_words"],
                interaction="summary",
                min_words=30,
                ordered=True,
            ),
            _two(
                "A water queue formed before opening time, and older residents could not reach the tap easily. The committee counted users for three mornings, created separate time slots, displayed the schedule, and asked for feedback after five days. Most users reported shorter waits.",
                "Summarise the change in order and identify the central improvement.",
                "The committee first measured the crowded queue, then introduced and displayed separate time slots. After five days it collected feedback, which showed shorter waits for most users. The central improvement was fairer, more orderly access to the tap.",
                ("sequence", "Orders measurement, schedule, and feedback.", "first measured the crowded queue, then introduced and displayed separate time slots. After five days it collected feedback"),
                ("improvement", "States the central access benefit.", "fairer, more orderly access to the tap"),
                skills=["reading.event_sequence", "writing.summary_own_words"],
                interaction="summary",
                min_words=34,
                ordered=True,
            ),
        ],
        "transfer": [
            _two(
                "A library received complaints about noise. Staff recorded the busiest times, spoke with student groups, moved group work to one room, and checked sound levels the following week.",
                "Transfer the problem-process-follow-up summary structure to this case.",
                "The library investigated noise complaints by recording busy times and hearing student groups. Staff moved group work to a separate room, then checked sound levels the next week to judge the change.",
                ("process", "Includes investigation and consultation.", "recording busy times and hearing student groups"),
                ("followup", "States the change and later check.", "moved group work to a separate room, then checked sound levels the next week"),
                skills=["reading.event_sequence", "writing.summary_own_words"],
                interaction="summary",
                min_words=28,
            ),
        ],
        "support": [
            _one(
                "First the complaint was written down. Next both neighbours spoke. Last the boundary stone was measured.",
                "List the three events in order.",
                "The complaint was recorded, both neighbours were heard, and the boundary stone was measured last.",
                "complaint was recorded, both neighbours were heard, and the boundary stone was measured last",
                description="Preserves all three ordered events.",
                skills=["reading.event_sequence"],
            ),
            _two(
                "A drain overflowed near the market. Workers cleared leaves that afternoon, and an inspector returned after rain to confirm that water flowed.",
                "State the problem, action, and follow-up.",
                "The market drain overflowed, so workers cleared the leaves. An inspector later checked the drain after rain and confirmed that it flowed.",
                ("response", "Links overflow to leaf removal.", "drain overflowed, so workers cleared the leaves"),
                ("check", "Includes the later rain check.", "inspector later checked the drain after rain and confirmed that it flowed"),
                skills=["reading.event_sequence", "writing.summary_own_words"],
            ),
            _one(
                "Both teams described the disputed score, the score sheet was examined, and one point was corrected.",
                "Write the main idea in one sentence.",
                "A disputed score was corrected after both teams were heard and the written record was checked.",
                "score was corrected after both teams were heard and the written record was checked",
                description="Summarises hearing, evidence, and correction.",
                skills=["writing.summary_own_words"],
            ),
            _two(
                "Parents requested a safer crossing. Officials watched traffic, painted a zebra crossing, and returned a month later to count safe crossings.",
                "Compress the sequence while keeping the follow-up.",
                "Officials responded to the safety request by observing traffic and painting a zebra crossing. A month later they counted crossings to review its use.",
                ("action", "Includes observation and crossing paint.", "observing traffic and painting a zebra crossing"),
                ("review", "Keeps the later count.", "month later they counted crossings to review its use"),
                skills=["reading.event_sequence", "writing.summary_own_words"],
            ),
            _one(
                "The meeting ended with a trial schedule, not a final rule. Members agreed to review it after seven days.",
                "State the outcome without claiming the rule was permanent.",
                "The members adopted a seven-day trial schedule and planned a review before making any permanent decision.",
                "adopted a seven-day trial schedule and planned a review before making any permanent decision",
                description="States the temporary outcome and review boundary.",
                skills=["writing.summary_own_words"],
            ),
        ],
    },
    "panchayat-dialogue-attribution": {
        "guided": [
            _one(
                "\"I measured the path this morning,\" said Iqbal. Meera replied, \"Please show the mark to the committee.\"",
                "Who asks to see the mark, and whom is she addressing?",
                "Meera asks Iqbal to show the measurement mark to the committee.",
                "Meera asks Iqbal to show the measurement mark",
                description="Identifies speaker, addressee, and request.",
                skills=["reading.dialogue_attribution"],
            ),
            _one(
                "The clerk told Rani, \"Your form is complete.\" She answered, \"Then I will submit it now.\"",
                "What does She refer to, and what is her purpose?",
                "She refers to Rani, whose reply states her intention to submit the completed form.",
                "She refers to Rani, whose reply states her intention to submit",
                description="Resolves the pronoun and response purpose.",
                skills=["reading.dialogue_attribution"],
            ),
        ],
        "independent": [
            _two(
                "\"The channel crossed my field before the new fence,\" Dev said. Tara answered, \"The survey map can settle that point.\" The chairperson then asked her to place the map on the table.",
                "Trace who speaks in the second sentence and what the chairperson's request refers to.",
                "Tara says that the survey map can settle the point. The chairperson's request to her means Tara should place that map on the table for examination.",
                ("speaker", "Identifies Tara and her claim.", "Tara says that the survey map can settle the point"),
                ("reference", "Resolves her and the requested object.", "request to her means Tara should place that map on the table"),
                skills=["reading.dialogue_attribution"],
                min_words=24,
            ),
            _two(
                "Aman said to the guard, \"I locked the gate at six.\" The guard replied, \"The logbook shows it reopened at seven.\" Sita asked him to read the second entry aloud.",
                "Identify him and explain how each speaker's contribution differs.",
                "Him refers to the guard, whom Sita asks to read the logbook entry. Aman reports his action, while the guard introduces written evidence that the gate reopened later.",
                ("referent", "Resolves him to the guard.", "Him refers to the guard, whom Sita asks to read the logbook entry"),
                ("roles", "Distinguishes personal report from documentary evidence.", "Aman reports his action, while the guard introduces written evidence"),
                skills=["reading.dialogue_attribution"],
                min_words=27,
            ),
        ],
        "transfer": [
            _two(
                "\"Our seed tray dried first,\" Lina told the science captain. He responded, \"Show me the watering chart.\" The teacher then asked Lina why it mattered.",
                "Resolve He and it, then state the purpose of both questions.",
                "He refers to the science captain, who requests the watering chart as evidence. It refers to the tray drying first, and the teacher asks Lina to explain why that observation matters.",
                ("references", "Resolves both pronouns.", "He refers to the science captain"),
                ("purposes", "Explains the evidence request and reason question.", "requests the watering chart as evidence. It refers to the tray drying first, and the teacher asks Lina to explain why that observation matters"),
                skills=["reading.dialogue_attribution"],
                min_words=27,
            ),
        ],
        "support": [
            _one(
                "\"I found the receipt,\" Kavya said. \"Please hand it to me,\" replied the clerk.",
                "Who wants the receipt?",
                "The clerk asks Kavya to hand over the receipt.",
                "clerk asks Kavya to hand over the receipt",
                description="Identifies the requesting speaker.",
                skills=["reading.dialogue_attribution"],
                min_words=8,
            ),
            _one(
                "Rohit told Mina, \"Your turn begins now.\" She picked up the marker.",
                "Who does She refer to?",
                "She refers to Mina, who picks up the marker for her turn.",
                "She refers to Mina",
                description="Resolves the pronoun through the addressee.",
                skills=["reading.dialogue_attribution"],
            ),
            _two(
                "\"The pipe is blocked,\" said the plumber. The caretaker answered, \"I will close the inlet.\"",
                "Name each speaker's purpose.",
                "The plumber reports the fault, while the caretaker states the immediate action she will take.",
                ("report", "Identifies the fault report.", "plumber reports the fault"),
                ("action", "Identifies the caretaker's response.", "caretaker states the immediate action"),
                skills=["reading.dialogue_attribution"],
            ),
            _one(
                "The judge asked Neel, \"Did you see the ball cross the line?\" He answered, \"Yes, from beside the post.\"",
                "Who is He and what evidence does he give?",
                "He is Neel, and he gives his viewing position beside the post as evidence.",
                "He is Neel, and he gives his viewing position beside the post",
                description="Resolves speaker and evidence.",
                skills=["reading.dialogue_attribution"],
            ),
            _two(
                "\"This key is mine,\" Leela told Omar. He replied, \"Then I will return it to you.\"",
                "Resolve He, it, and you.",
                "He refers to Omar, it refers to the key, and you refers to Leela.",
                ("people", "Resolves He and you.", "He refers to Omar"),
                ("object", "Resolves it to the key.", "it refers to the key"),
                skills=["reading.dialogue_attribution"],
            ),
        ],
    },
    "panchayat-fairness-reasoning": {
        "guided": [
            _two(
                "A captain gave her own team extra time without hearing the other side. No written rule allowed the change.",
                "Judge the process using one evidence clue and one fairness principle.",
                "The process was unfair because only one team received extra time and the other side was not heard. The same announced rule should apply to both teams.",
                ("evidence", "Uses unequal time or missing hearing.", "only one team received extra time and the other side was not heard"),
                ("principle", "States equal rule application.", "same announced rule should apply to both teams"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
            _two(
                "Two vendors disputed a stall. The committee heard both, checked dated receipts, and explained why the earlier valid receipt determined the temporary allocation.",
                "Identify two features that make the decision reasoned rather than status-based.",
                "The committee heard both vendors and checked dated receipts before deciding. It also explained the evidence-based reason instead of favouring either person's status.",
                ("process", "Uses hearing and receipt evidence.", "heard both vendors and checked dated receipts"),
                ("reason", "Contrasts evidence with status.", "explained the evidence-based reason instead of favouring either person's status"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
        ],
        "independent": [
            _two(
                "A student was blamed for damaging a window because he stood nearby. The review later found a time-stamped photograph showing the crack before he arrived, but the first decision had been announced without asking him to respond.",
                "Evaluate the first decision and propose a fair repair.",
                "The first decision was unfair because proximity was treated as proof and the student was not heard. The committee should withdraw the blame, record the photograph, hear the student, and reconsider the case from verified evidence.",
                ("failure", "Explains weak evidence and missing hearing.", "proximity was treated as proof and the student was not heard"),
                ("repair", "Proposes correction, record, hearing, and review.", "withdraw the blame, record the photograph, hear the student, and reconsider the case from verified evidence"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=31,
            ),
            _two(
                "A water schedule gave the first lane two hours and every other lane thirty minutes. Records showed similar household numbers, and no reason for the difference was published.",
                "Decide whether the rule is fair and state a defensible next step.",
                "The schedule is not justified because similar lanes receive sharply unequal time without a stated reason. Officials should compare need data, hear each lane, publish one consistent rule, and review the result after a trial.",
                ("judgment", "Uses unequal treatment and absent reasons.", "similar lanes receive sharply unequal time without a stated reason"),
                ("next", "Proposes evidence, hearing, consistent rule, and review.", "compare need data, hear each lane, publish one consistent rule, and review the result after a trial"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=31,
            ),
        ],
        "transfer": [
            _two(
                "A school club selected only the teacher's recommendations without reading anonymous applications. The published criteria required project evidence and a short statement from every applicant.",
                "Transfer the fairness test and propose a correction.",
                "The selection was unfair because it ignored the published criteria and excluded most applicants' evidence. The club should score every application against the same criteria, record reasons, and allow a review of errors.",
                ("problem", "Identifies ignored criteria and excluded evidence.", "ignored the published criteria and excluded most applicants' evidence"),
                ("correction", "Applies equal scoring, reasons, and review.", "score every application against the same criteria, record reasons, and allow a review of errors"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=28,
            ),
        ],
        "support": [
            _two(
                "Only one neighbour was allowed to speak before a boundary decision.",
                "Name the missing safeguard and a fair immediate action.",
                "The missing safeguard is hearing both sides. The decision should pause until the other neighbour can present evidence.",
                ("safeguard", "Names hearing both sides.", "missing safeguard is hearing both sides"),
                ("action", "Pauses for evidence.", "decision should pause until the other neighbour can present evidence"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
            _two(
                "A written rule says every late form is reviewed by the same two officers. The chair secretly approves a friend's late form alone.",
                "Explain the unequal treatment and the proper repair.",
                "The chair bypassed the common two-officer review for a friend. The form should return to the ordinary review and the exception should be recorded.",
                ("breach", "Identifies the bypassed common process.", "bypassed the common two-officer review for a friend"),
                ("repair", "Restores ordinary review and a record.", "form should return to the ordinary review and the exception should be recorded"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
            _two(
                "Both teams were heard, but the final score correction gave no reason and cited no score sheet.",
                "What is still missing, and what should the decision include?",
                "A reason tied to evidence is still missing. The correction should cite the score-sheet entry and explain how it changes the result.",
                ("missing", "Identifies absent evidence-based reasons.", "reason tied to evidence is still missing"),
                ("needed", "Requires citation and explanation.", "cite the score-sheet entry and explain how it changes the result"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
            _two(
                "A temporary queue rule worked for two days, but no one checked whether older users could access the counter.",
                "State the follow-up gap and one review step.",
                "The process lacks a check on access for older users. Staff should observe the queue, collect their feedback, and revise the rule if the barrier continues.",
                ("gap", "Names the untested access issue.", "lacks a check on access for older users"),
                ("review", "Proposes observation, feedback, and revision.", "observe the queue, collect their feedback, and revise the rule"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
            _two(
                "A clerk corrects an incorrect fine but leaves the false reason in the public record.",
                "Explain why the repair is incomplete and what must change.",
                "The repair is incomplete because the false reason can still harm the person. The clerk must correct the public record and notify the affected person.",
                ("harm", "Explains continuing record harm.", "false reason can still harm the person"),
                ("repair", "Requires record correction and notice.", "correct the public record and notify the affected person"),
                skills=["reading.inference_reason", "writing.reason_answer"],
            ),
        ],
    },
    "panchayat-language-relations": {
        "guided": [
            _one(
                "The notice board hangs ___ the clerk's desk, high on the wall.",
                "Complete the sentence with the relation word supported by the position clue.",
                "The notice board hangs above the clerk's desk.",
                "notice board hangs above the clerk's desk",
                description="Uses above for a higher position.",
                skills=["grammar.prepositions", "reading.word_meaning_context"],
                min_words=8,
            ),
            _one(
                "The witness stood beside the doorway, close enough to hear the conversation.",
                "What does beside mean in this context?",
                "Beside means next to the doorway.",
                "Beside means next to the doorway",
                description="Infers the spatial relation from context.",
                skills=["reading.word_meaning_context", "grammar.prepositions"],
                min_words=6,
            ),
        ],
        "independent": [
            _two(
                "The evidence box was placed between the chairperson and the clerk, while the map hung behind them on the wall.",
                "Explain both relations and rewrite them as complete location sentences.",
                "The evidence box was in the middle of the chairperson and clerk. The map was on the wall at their back.",
                ("between", "Explains the middle position.", "evidence box was in the middle of the chairperson and clerk"),
                ("behind", "Explains the rear position.", "map was on the wall at their back"),
                skills=["reading.word_meaning_context", "grammar.prepositions"],
                min_words=20,
            ),
            _two(
                "A folder lay beneath the register, and a sealed envelope was tucked inside the folder.",
                "Distinguish beneath and inside using the two objects.",
                "The folder was under the register, which explains beneath. The envelope was enclosed by the folder, which explains inside.",
                ("beneath", "Paraphrases the lower position.", "folder was under the register"),
                ("inside", "Paraphrases enclosure.", "envelope was enclosed by the folder"),
                skills=["reading.word_meaning_context", "grammar.prepositions"],
                min_words=18,
            ),
        ],
        "transfer": [
            _two(
                "In the lab, a thermometer stands among three beakers, and the safety sheet is pinned above the sink.",
                "Transfer both relation words into clear explanations.",
                "Among means the thermometer is surrounded by the three beakers. Above means the safety sheet is higher than the sink.",
                ("among", "Explains surrounded position.", "thermometer is surrounded by the three beakers"),
                ("above", "Explains higher position.", "safety sheet is higher than the sink"),
                skills=["reading.word_meaning_context", "grammar.prepositions"],
            ),
        ],
        "support": [
            _one(
                "The stamp is inside the drawer.",
                "Explain inside using a simpler phrase.",
                "The drawer contains the stamp in its enclosed space.",
                "drawer contains the stamp",
                description="Explains enclosure.",
                skills=["reading.word_meaning_context"],
                min_words=6,
            ),
            _one(
                "The bench is opposite the water counter.",
                "What does opposite tell us about the bench?",
                "The bench faces the water counter from the other side.",
                "bench faces the water counter from the other side",
                description="Explains the facing relation.",
                skills=["reading.word_meaning_context", "grammar.prepositions"],
            ),
            _one(
                "The receipt slipped under the file.",
                "Replace under with a phrase that keeps the relation.",
                "The receipt slipped to a lower position beneath the file.",
                "lower position beneath the file",
                description="Restates the lower relation.",
                skills=["reading.word_meaning_context", "grammar.prepositions"],
            ),
            _one(
                "The two speakers stood on either side of the table.",
                "Complete this equivalent sentence: The table stood ___ them.",
                "The table stood between them, separating their two positions.",
                "table stood between them",
                description="Uses between for two sides.",
                skills=["grammar.prepositions"],
                min_words=6,
            ),
            _two(
                "A queue forms along the wall and ends near the entrance.",
                "Explain along and near separately.",
                "Along means the queue follows the wall's length. Near means its end is close to the entrance.",
                ("along", "Explains following a length.", "queue follows the wall's length"),
                ("near", "Explains closeness.", "end is close to the entrance"),
                skills=["reading.word_meaning_context", "grammar.prepositions"],
            ),
        ],
    },
    "panchayat-past-chronology": {
        "guided": [
            _one(
                "By the time the meeting began, the clerk had already copied the complaint.",
                "Which event happened first, and which verb form proves it?",
                "The clerk copied the complaint first; had copied marks the earlier completed past event.",
                "clerk copied the complaint first; had copied marks the earlier completed past event",
                description="Identifies the earlier event and tense clue.",
                skills=["grammar.tense_usage"],
            ),
            _one(
                "The inspector arrived after the workers had cleared the blocked drain.",
                "Rewrite the events from first to later.",
                "The workers had cleared the drain first, and the inspector arrived later.",
                "workers had cleared the drain first, and the inspector arrived later",
                description="Orders the two past events.",
                skills=["grammar.tense_usage"],
            ),
        ],
        "independent": [
            _two(
                "The team presented the new map at noon. Earlier, the surveyor had measured every boundary point and had signed the field notes.",
                "Write two sentences that make the earlier evidence work and later presentation clear.",
                "The surveyor had measured every boundary point and signed the field notes before noon. The team presented that completed map later at the meeting.",
                ("earlier", "Uses past perfect for completed preparation.", "surveyor had measured every boundary point and signed the field notes before noon"),
                ("later", "Uses simple past for the presentation.", "team presented that completed map later"),
                skills=["grammar.tense_usage"],
                min_words=21,
                ordered=True,
            ),
            _two(
                "When Kavita reached the office, the courier left the parcel at the desk. The intended meaning is that the parcel was already there before Kavita arrived.",
                "Correct the tense and explain the event order.",
                "When Kavita reached the office, the courier had already left the parcel at the desk. Had left shows that delivery happened before her arrival.",
                ("correction", "Uses had left for the earlier event.", "courier had already left the parcel"),
                ("order", "Explains delivery before arrival.", "delivery happened before her arrival"),
                skills=["grammar.tense_usage"],
                min_words=21,
                ordered=True,
            ),
        ],
        "transfer": [
            _two(
                "The seedlings bent during the storm, but the class had tied support sticks beside them the previous day.",
                "Explain which preparation happened first and how the tenses show it.",
                "The class had tied the support sticks first, on the previous day. The seedlings bent later during the storm, so past perfect marks preparation before the simple-past event.",
                ("first", "Identifies the earlier preparation.", "class had tied the support sticks first"),
                ("contrast", "Explains the tense relationship.", "past perfect marks preparation before the simple-past event"),
                skills=["grammar.tense_usage"],
                min_words=25,
            ),
        ],
        "support": [
            _one(
                "The bell rang after the chairperson had entered.",
                "Which action came first?",
                "The chairperson had entered first, and the bell rang later.",
                "chairperson had entered first, and the bell rang later",
                description="Orders entry before the bell.",
                skills=["grammar.tense_usage"],
            ),
            _one(
                "Before the bus arrived, the children had formed a queue.",
                "State the earlier completed action.",
                "The children had formed the queue before the bus arrived.",
                "children had formed the queue before the bus arrived",
                description="Identifies the earlier action.",
                skills=["grammar.tense_usage"],
            ),
            _two(
                "The clerk filed the form after she had checked the signature.",
                "Name the first and second events.",
                "She had checked the signature first. The clerk filed the form second.",
                ("first", "Identifies checking first.", "checked the signature first"),
                ("second", "Identifies filing second.", "filed the form second"),
                skills=["grammar.tense_usage"],
                min_words=12,
            ),
            _one(
                "Draft: The rain stopped after the workers cleared the drain. Intended order: clearing was complete before the rain stopped.",
                "Use past perfect to make the intended order explicit.",
                "The rain stopped after the workers had cleared the drain.",
                "workers had cleared the drain",
                description="Uses past perfect for earlier clearing.",
                skills=["grammar.tense_usage"],
            ),
            _two(
                "At six, the gate opened. The guard had unlocked it five minutes earlier.",
                "Explain the two times and tense forms.",
                "The guard had unlocked the gate first at 5:55. The gate opened later at six.",
                ("earlier", "Places unlocking at 5:55.", "unlocked the gate first at 5:55"),
                ("later", "Places opening at six.", "gate opened later at six"),
                skills=["grammar.tense_usage"],
            ),
        ],
    },
    "panchayat-clue-prediction": {
        "guided": [
            _one(
                "Dark clouds gather, vendors cover their baskets, and a cool wind lifts dust from the lane.",
                "Predict one immediate event supported by the clues.",
                "Rain is likely to begin soon because the clouds, covered baskets, and cool wind all signal an approaching shower.",
                "Rain is likely to begin soon because the clouds, covered baskets, and cool wind",
                description="Makes a bounded weather prediction from multiple clues.",
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
            ),
            _one(
                "The clerk brings the missing register, both parties lean toward it, and the chairperson asks for silence.",
                "What is most likely to happen next?",
                "The register will probably be examined next because it has just been brought forward as relevant evidence.",
                "register will probably be examined next",
                description="Predicts evidence examination from the action clues.",
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
            ),
        ],
        "independent": [
            _two(
                "The lane committee has finished hearing residents. A map and two dated photographs lie open on the table, and the chairperson asks members to compare the marked boundary points.",
                "Predict the next procedural step and state one detail that remains unknown.",
                "The members will probably compare the map with the dated photographs before giving a reasoned boundary decision. The clues do not reveal which side will ultimately succeed.",
                ("prediction", "Predicts comparison before decision.", "compare the map with the dated photographs before giving a reasoned boundary decision"),
                ("limit", "States the unknown final winner.", "do not reveal which side will ultimately succeed"),
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
                min_words=24,
            ),
            _two(
                "A repaired tap has been tested twice without leaking. The caretaker dries the floor, removes the warning sign, and asks the clerk to update the maintenance log.",
                "Predict the next action and explain the evidence chain.",
                "The clerk will likely record the repair as complete because repeated tests show no leak and the warning sign has been removed. A future leak cannot be ruled out from this short test.",
                ("prediction", "Predicts completion record.", "clerk will likely record the repair as complete"),
                ("boundary", "Limits certainty beyond the current test.", "future leak cannot be ruled out from this short test"),
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
                min_words=27,
            ),
        ],
        "transfer": [
            _two(
                "In a science trial, the shaded seedling remains green while the unwatered seedling droops. The group prepares a measuring scale and opens its observation table.",
                "Predict the next evidence-gathering action and avoid predicting a final conclusion.",
                "The group will probably measure both seedlings and record the results in the table. The clues do not yet prove the final cause of every difference.",
                ("action", "Predicts measurement and recording.", "measure both seedlings and record the results in the table"),
                ("limit", "Avoids a premature causal conclusion.", "do not yet prove the final cause of every difference"),
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
                min_words=22,
            ),
        ],
        "support": [
            _one(
                "A player places the ball on the spot and steps back for a run-up.",
                "What will probably happen next?",
                "The player will probably run forward and kick the ball.",
                "player will probably run forward and kick the ball",
                description="Predicts the immediate action from setup clues.",
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
            ),
            _one(
                "The power fails, the room becomes dark, and the guard reaches for a torch.",
                "Predict the guard's next action.",
                "The guard will probably switch on the torch to see in the dark room.",
                "guard will probably switch on the torch",
                description="Uses the darkness and torch clue.",
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
            ),
            _two(
                "The committee has heard only the first speaker, while three others wait with documents.",
                "Predict the fair next step and state what cannot be decided yet.",
                "The committee should hear the waiting speakers and examine their documents next. A final decision cannot fairly be predicted before that evidence is considered.",
                ("next", "Predicts hearing and document review.", "hear the waiting speakers and examine their documents next"),
                ("limit", "Blocks premature decision.", "final decision cannot fairly be predicted before that evidence is considered"),
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
            ),
            _one(
                "A kettle whistles and steam rises from its spout.",
                "What safe action is likely next?",
                "An adult will likely switch off the heat and move the kettle safely.",
                "adult will likely switch off the heat and move the kettle safely",
                description="Makes a safe immediate prediction.",
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
            ),
            _two(
                "The scoreboard is tied with one turn remaining, and the final player walks to the throwing line.",
                "Predict the next event without predicting the winner.",
                "The final player will take the remaining turn next. The tied score does not reveal whether the throw will win, lose, or keep the tie.",
                ("event", "Predicts the final turn.", "final player will take the remaining turn next"),
                ("limit", "Keeps the outcome open.", "does not reveal whether the throw will win, lose, or keep the tie"),
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
            ),
        ],
    },
    "panchayat-first-person-letter": {
        "guided": [
            _two(
                "You are Reena. A delivery cart repeatedly blocks the gate to your lane, delaying the school bus. Write to the ward office asking for a timed loading space.",
                "Write the opening and request in Reena's voice.",
                "Dear Ward Officer, I live beside the lane gate, where a delivery cart blocks our school bus each morning. Please mark a timed loading space so the gate remains clear during bus hours.",
                ("voice", "Uses I and describes Reena's direct experience.", "I live beside the lane gate, where a delivery cart blocks our school bus each morning"),
                ("request", "Makes the timed-loading request with purpose.", "Please mark a timed loading space so the gate remains clear during bus hours"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=29,
            ),
            _two(
                "You are Mohit. The community tap was repaired after your complaint. Write a short thank-you note that also asks when the final inspection will occur.",
                "Write two respectful sentences and a closing.",
                "Dear Maintenance Team, Thank you for repairing the tap after I reported the leak. Please tell me when the final inspection will take place. Sincerely, Mohit",
                ("thanks", "Thanks the team from Mohit's viewpoint.", "Thank you for repairing the tap after I reported the leak"),
                ("question", "Asks respectfully about inspection.", "Please tell me when the final inspection will take place"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=24,
            ),
        ],
        "independent": [
            _two(
                "You are Saira, whose name was wrongly placed on a late-payment list. You submitted the receipt on time and have a dated copy. Write to the records clerk requesting correction and confirmation.",
                "Write a complete first-person letter with evidence, impact, request, and respectful close.",
                "Dear Records Clerk, My name was wrongly placed on the late-payment list even though I submitted the receipt on time. I have attached my dated copy, and the incorrect entry has caused confusion at the office. Please correct the public record and confirm the change in writing. Sincerely, Saira",
                ("case", "States Saira's experience and dated evidence.", "My name was wrongly placed on the late-payment list even though I submitted the receipt on time. I have attached my dated copy"),
                ("request", "Requests record correction and confirmation.", "Please correct the public record and confirm the change in writing"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=44,
            ),
            _two(
                "You are Arvind. A trial queue schedule reduced your wait, but your grandmother still cannot stand for long. Write to the committee suggesting a seated token system during the next trial.",
                "Write a balanced letter that notes progress and proposes the next improvement.",
                "Dear Committee Members, The trial schedule has reduced my waiting time, and I appreciate that improvement. My grandmother still finds it difficult to stand in the queue for long. Please test a seated token system during the next trial so older residents can wait safely. Regards, Arvind",
                ("experience", "States improvement and remaining difficulty.", "trial schedule has reduced my waiting time"),
                ("proposal", "Requests a seated token trial with a reason.", "Please test a seated token system during the next trial so older residents can wait safely"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=42,
            ),
        ],
        "transfer": [
            _two(
                "You are the captain of a science club. A promised room was locked during your exhibition, so visitors could not see the projects. Write to the principal asking for a rescheduled slot and a named contact.",
                "Transfer the evidence-request-close structure to this school letter.",
                "Dear Principal, Our exhibition room was locked during the promised slot, so visitors could not see the science projects we had prepared. Please give the club a new exhibition time and name the staff member who will confirm access. Sincerely, The Science Club Captain",
                ("impact", "Explains the locked room and missed exhibition.", "room was locked during the promised slot, so visitors could not see the science projects"),
                ("request", "Asks for a new time and named contact.", "Please give the club a new exhibition time and name the staff member who will confirm access"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=39,
            ),
        ],
        "support": [
            _two(
                "You are Nila. The park tap leaks every afternoon. Ask the caretaker to inspect it.",
                "Write a greeting, problem sentence, and request.",
                "Dear Caretaker, I have seen the park tap leak every afternoon. Please inspect it and stop the water loss. Regards, Nila",
                ("problem", "Uses I to state the observed leak.", "I have seen the park tap leak every afternoon"),
                ("request", "Makes a polite inspection request.", "Please inspect it and stop the water loss"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
            ),
            _two(
                "You are Kabir. A neighbour returned your lost notebook.",
                "Write a short thank-you message with one specific detail.",
                "Dear Mr Sen, Thank you for returning the notebook I lost near the bus stop. Your help saved my class notes. Warmly, Kabir",
                ("thanks", "Thanks the neighbour for the exact action.", "Thank you for returning the notebook I lost near the bus stop"),
                ("detail", "States why the return mattered.", "Your help saved my class notes"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
            ),
            _two(
                "You are Tara. The meeting notice gives the date but no starting time.",
                "Ask the clerk for the missing information in a respectful note.",
                "Dear Clerk, I received the meeting notice for 22 August, but it does not include a starting time. Please tell me when the meeting begins. Sincerely, Tara",
                ("gap", "States the missing time.", "does not include a starting time"),
                ("request", "Asks when the meeting begins.", "Please tell me when the meeting begins"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
            ),
            _two(
                "You are Imran. A trial traffic barrier made your walk safer.",
                "Write feedback that names the benefit and asks for a review date.",
                "Dear Traffic Team, The trial barrier has made my walk across the lane safer. Please let residents know when its results will be reviewed. Regards, Imran",
                ("benefit", "States the personal safety benefit.", "made my walk across the lane safer"),
                ("question", "Asks for the review timing.", "Please let residents know when its results will be reviewed"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
            ),
            _two(
                "You are Pooja. Your address is misspelled on a library card.",
                "Write a correction request and include the correct spelling: 18 Neem Lane.",
                "Dear Librarian, My address is misspelled on the library card. Please correct it to 18 Neem Lane and confirm the updated card. Sincerely, Pooja",
                ("error", "States the misspelled address problem.", "address is misspelled on the library card"),
                ("correction", "Provides the correct address and asks for confirmation.", "Please correct it to 18 Neem Lane and confirm the updated card"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
            ),
        ],
    },
    "panchayat-less-words": {
        "guided": [
            _one(
                "After the batteries died, the torch was ___ and could not light the path. Base noun: power.",
                "Form the correct -less word and use it in the sentence.",
                "The torch was powerless and could not light the path.",
                "torch was powerless and could not light the path",
                description="Forms powerless with the correct meaning.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
            _one(
                "A statement with no care for the facts was described as ___. Base noun: care.",
                "Build the -less adjective that fits.",
                "The statement was careless because it ignored the facts.",
                "statement was careless because it ignored the facts",
                description="Forms careless and uses the context clue.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=8,
            ),
        ],
        "independent": [
            _two(
                "The waiting room had no windows, and the air felt stale. A draft calls it windowless and hopeless, but only one word directly describes the room's physical feature.",
                "Choose the precise -less word and explain why the other claim is unsupported.",
                "Windowless precisely means that the room has no windows. Hopeless describes lack of hope, which the passage does not establish about the people or situation.",
                ("word", "Defines windowless from the physical clue.", "Windowless precisely means that the room has no windows"),
                ("limit", "Rejects unsupported hopeless.", "Hopeless describes lack of hope, which the passage does not establish"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=24,
            ),
            _two(
                "A cyclist rode without fear after checking the safe empty path. Another learner wrote fearles, while a third used fearless correctly.",
                "Correct the spelling and explain the suffix meaning.",
                "Fearless is the correct spelling. It means without fear, which fits the cyclist's confidence after the safety check.",
                ("spelling", "Gives the correctly spelled word.", "Fearless is the correct spelling"),
                ("meaning", "Explains without fear from context.", "means without fear, which fits the cyclist's confidence"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=18,
            ),
        ],
        "transfer": [
            _two(
                "A digital file opened with no title at the top. The editor called it nameless, but did not claim that its author was unknown.",
                "Explain the valid meaning and its boundary.",
                "Nameless means the file has no displayed name or title. It does not prove that the author is unknown.",
                ("meaning", "Explains absence of a displayed name.", "file has no displayed name or title"),
                ("boundary", "Rejects the author inference.", "does not prove that the author is unknown"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
        ],
        "support": [
            _one(
                "A cup without water is ___. Base noun: water.",
                "Form the -less adjective.",
                "The cup is waterless because it contains no water.",
                "cup is waterless because it contains no water",
                description="Forms waterless from the supplied meaning.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=8,
            ),
            _one(
                "A wireless radio uses no connecting wire.",
                "Explain the suffix meaning in wireless.",
                "Wireless means operating without a connecting wire.",
                "Wireless means operating without a connecting wire",
                description="Explains without the base noun.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=7,
            ),
            _one(
                "The moonless night had no moon visible.",
                "Identify the base noun and meaning.",
                "The base noun is moon, and moonless means without visible moonlight.",
                "moonless means without visible moonlight",
                description="Connects base noun and suffix meaning.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
            _two(
                "A careless mistake happened because the form was signed without checking the date.",
                "Explain careless and cite the action clue.",
                "Careless means showing too little care. Signing without checking the date is the clue.",
                ("meaning", "Explains lack of care.", "Careless means showing too little care"),
                ("clue", "Uses the unchecked date action.", "Signing without checking the date is the clue"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
            _two(
                "A spotless plate has no spots after washing, but that does not mean it is new.",
                "Explain the valid meaning and limit.",
                "Spotless means having no visible spots. The word does not prove that the plate is new.",
                ("meaning", "Defines absence of spots.", "Spotless means having no visible spots"),
                ("limit", "Rejects the age claim.", "does not prove that the plate is new"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
        ],
    },
    "panchayat-bounded-research": {
        "guided": [
            _two(
                "Source card: The reading room opened in 2016, has forty seats, and closes at seven in the evening. The card does not name its architect.",
                "Report two facts and one source limit.",
                "According to the source card, the reading room opened in 2016 and has forty seats. The architect cannot be identified from this card.",
                ("facts", "Reports two supplied facts.", "reading room opened in 2016 and has forty seats"),
                ("limit", "States the missing architect.", "architect cannot be identified from this card"),
                skills=["research.information_selection"],
            ),
            _two(
                "Observation note: At 8:00, twelve people waited at the counter; at 8:30, five waited. No reason for the change was recorded.",
                "State the observed change and avoid an unsupported cause.",
                "The recorded queue fell from twelve people at 8:00 to five at 8:30. The note does not establish why the queue became shorter.",
                ("observation", "Reports both counts and times.", "queue fell from twelve people at 8:00 to five at 8:30"),
                ("limit", "Rejects an invented cause.", "does not establish why the queue became shorter"),
                skills=["research.information_selection"],
            ),
        ],
        "independent": [
            _two(
                "Packet A: a dated receipt records payment on 3 June. Packet B: a clerk's note says the account was marked late on 5 June. Neither packet explains who entered the late mark.",
                "Write a two-source report that separates facts from the unresolved responsibility.",
                "Packet A records payment on 3 June, while Packet B records a late mark dated 5 June. Together they show the payment predates the late mark, but they do not identify who entered that mark.",
                ("comparison", "Accurately combines both dated facts.", "payment on 3 June, while Packet B records a late mark dated 5 June"),
                ("limit", "Keeps responsibility unresolved.", "do not identify who entered that mark"),
                skills=["research.information_selection"],
                min_words=30,
            ),
            _two(
                "Survey summary: 28 of 40 respondents preferred morning collection; 9 preferred evening; 3 gave no preference. The survey included only households on two lanes.",
                "Report the result and state the sampling boundary.",
                "The survey found that 28 of 40 respondents preferred morning collection, compared with 9 choosing evening and 3 giving no preference. The result represents only the households surveyed on two lanes and cannot automatically describe the whole town.",
                ("result", "Reports all three counts accurately.", "28 of 40 respondents preferred morning collection, compared with 9 choosing evening and 3 giving no preference"),
                ("boundary", "Limits the claim to the sample.", "represents only the households surveyed on two lanes and cannot automatically describe the whole town"),
                skills=["research.information_selection"],
                min_words=35,
            ),
        ],
        "transfer": [
            _two(
                "Plant trial log: Pot A received 100 ml daily and grew 4 cm; Pot B received 50 ml daily and grew 2 cm over the same week. Soil type was not recorded.",
                "Write a bounded comparison and avoid claiming a complete cause.",
                "In this one-week log, Pot A received more water and grew 2 cm more than Pot B. Because soil type was not recorded, the log alone cannot prove that water amount caused the entire difference.",
                ("comparison", "Reports treatment and growth difference.", "Pot A received more water and grew 2 cm more than Pot B"),
                ("limit", "States the missing-control boundary.", "soil type was not recorded, the log alone cannot prove that water amount caused the entire difference"),
                skills=["research.information_selection"],
                min_words=30,
            ),
        ],
        "support": [
            _two(
                "Card: The bridge is 18 metres long and was repaired in 2024. Its builder is not listed.",
                "Report one fact and one limit.",
                "The card says the bridge is 18 metres long and was repaired in 2024. It does not name the builder.",
                ("facts", "Reports supplied measurements or date.", "bridge is 18 metres long and was repaired in 2024"),
                ("limit", "States the absent builder.", "does not name the builder"),
                skills=["research.information_selection"],
            ),
            _two(
                "Count sheet: 16 bicycles passed before noon and 11 after noon. Weather was not recorded.",
                "Compare the counts and state what is unknown.",
                "Five more bicycles passed before noon than after noon. The sheet gives no weather information.",
                ("comparison", "Calculates the count difference.", "Five more bicycles passed before noon than after noon"),
                ("limit", "States missing weather data.", "gives no weather information"),
                skills=["research.information_selection"],
            ),
            _two(
                "Interview note: The gardener waters at six each morning and uses two cans. The note does not measure litres.",
                "Attribute the routine and avoid inventing volume.",
                "According to the interview note, the gardener waters at six with two cans. The number of litres is unknown.",
                ("routine", "Attributes time and cans.", "gardener waters at six with two cans"),
                ("limit", "Keeps litres unknown.", "number of litres is unknown"),
                skills=["research.information_selection"],
            ),
            _two(
                "Map key: blue marks public wells and green marks parks. The map has no dates.",
                "Explain two supported meanings and the time limit.",
                "Blue symbols identify public wells, and green symbols identify parks. The map cannot show when either feature was built.",
                ("meanings", "Reports both map-key facts.", "Blue symbols identify public wells, and green symbols identify parks"),
                ("limit", "Rejects construction dates.", "cannot show when either feature was built"),
                skills=["research.information_selection"],
            ),
            _two(
                "Two photographs show the same lane before and after a barrier was installed. They show fewer parked carts later but contain no traffic counts.",
                "State the visible difference and avoid a numerical claim.",
                "The later photograph visibly shows fewer parked carts than the earlier one. The photographs do not provide exact traffic counts.",
                ("observation", "Reports the visible comparison.", "later photograph visibly shows fewer parked carts"),
                ("limit", "Rejects exact counts.", "do not provide exact traffic counts"),
                skills=["research.information_selection"],
            ),
        ],
    },
}


_LAUNCH_VARIANTS = {
    "panchayat-sequence-summary": {
        "transfer": [
            _two(
                "Residents reported that a shared water pipe leaked beside the apartment gate. The manager logged the complaint, a plumber inspected the joint, the joint was replaced, and the manager checked the ground two days later for fresh dampness.",
                "Summarise the problem, response, and follow-up in the correct order.",
                "A leaking pipe was reported and formally logged before a plumber inspected and replaced the damaged joint. Two days later, the manager checked for damp ground to confirm whether the repair had worked.",
                ("response", "Orders reporting, inspection, and repair.", "reported and formally logged before a plumber inspected and replaced the damaged joint"),
                ("followup", "Includes the later check and its purpose.", "manager checked for damp ground to confirm whether the repair had worked"),
                skills=["reading.event_sequence", "writing.summary_own_words"],
                interaction="summary",
                min_words=30,
                ordered=True,
            ),
        ],
        "review": [
            _two(
                "Bus riders asked for shade at an exposed stop. The ward team counted afternoon users, compared two safe locations, installed a canopy, and asked riders for feedback after one hot week.",
                "Write a concise summary that keeps the request, evidence, action, and review in order.",
                "Riders requested shade, so the ward team counted users and compared safe sites before installing a canopy. After a hot week, the team collected feedback to review whether the new shade helped.",
                ("sequence", "Orders request, evidence, and installation.", "requested shade, so the ward team counted users and compared safe sites before installing a canopy"),
                ("review", "Includes the later feedback check.", "After a hot week, the team collected feedback to review whether the new shade helped"),
                skills=["reading.event_sequence", "writing.summary_own_words"],
                interaction="summary",
                min_words=30,
                ordered=True,
            ),
            _two(
                "Vendors complained that loose waste blocked a market drain. The committee heard cleaners and shopkeepers, inspected the lane after closing, placed covered bins at two corners, and reviewed the drain after the next market day.",
                "Summarise the complete change without copying the original sentence structure.",
                "After hearing both groups and inspecting the closed market, the committee added covered bins at two corners. It then checked the drain after another market day to see whether the blockage had decreased.",
                ("process", "Includes consultation, inspection, and action.", "hearing both groups and inspecting the closed market, the committee added covered bins"),
                ("check", "States the follow-up and its purpose.", "checked the drain after another market day to see whether the blockage had decreased"),
                skills=["reading.event_sequence", "writing.summary_own_words"],
                interaction="summary",
                min_words=31,
                ordered=True,
            ),
        ],
    },
    "panchayat-dialogue-attribution": {
        "transfer": [
            _one(
                "'The notice is too high for me to read,' Asha told the clerk. He replied, 'I will place another copy beside the ramp this afternoon.'",
                "Identify who raises the problem, who promises action, and what each speaker means.",
                "Asha tells the clerk that she cannot easily read the high notice. The clerk promises to place a second copy beside the ramp that afternoon.",
                "Asha tells the clerk that she cannot easily read the high notice. The clerk promises to place a second copy beside the ramp",
                description="Attributes both statements and their purposes correctly.",
                skills=["reading.dialogue_attribution"],
                min_words=23,
            ),
        ],
        "review": [
            _one(
                "Rohan asked Mira, 'Did your group record the tap readings?' She answered, 'Yes, I gave our table to the science teacher.'",
                "Who asks for information, who answers, and what does our refer to?",
                "Rohan asks whether Mira's group recorded the readings. Mira confirms that they did, and our refers to the table made by Mira and her group.",
                "Rohan asks whether Mira's group recorded the readings. Mira confirms that they did, and our refers to the table made by Mira and her group",
                description="Uses names, pronouns, and response links to attribute the exchange.",
                skills=["reading.dialogue_attribution"],
                min_words=24,
            ),
            _one(
                "'Please keep the side gate clear during delivery time,' the guard said to the driver. 'I will park beside the marked wall instead,' the driver replied.",
                "State the guard's request and the driver's response without mixing up the speakers.",
                "The guard asks the driver not to block the side gate during deliveries. The driver agrees to park beside the marked wall instead.",
                "guard asks the driver not to block the side gate during deliveries. The driver agrees to park beside the marked wall",
                description="Attributes the request and agreement to the correct speakers.",
                skills=["reading.dialogue_attribution"],
                min_words=22,
            ),
        ],
    },
    "panchayat-fairness-reasoning": {
        "transfer": [
            _two(
                "Three students requested the only library computer at the same time. The monitor checked the booking sheet, found that one name had been entered first, and offered the other two equal later slots. A torn corner hid part of one entry, so the librarian verified it before confirming the order.",
                "Judge whether the process is fair and support the judgment with two specific safeguards.",
                "The process is fair because the booking order is checked rather than decided by friendship or status. The librarian also verifies the damaged entry and gives the remaining students equal later slots.",
                ("rule", "Identifies the neutral rule used for the decision.", "booking order is checked rather than decided by friendship or status"),
                ("safeguards", "Uses verification and equal alternatives as evidence.", "verifies the damaged entry and gives the remaining students equal later slots"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=29,
            ),
        ],
        "review": [
            _two(
                "Two teams asked to use new sports cones. The captain's team was not chosen automatically; the teacher counted each team's previous turns, heard both requests, and gave the cones first to the team that had waited longer. The other team received the next slot in writing.",
                "Explain why the allocation is fair, using the process rather than the teams' popularity.",
                "The teacher applies the same waiting-time record to both teams and hears both requests before deciding. Giving the other team a written next slot also makes the remedy clear and equal.",
                ("process", "Identifies equal evidence and hearing.", "applies the same waiting-time record to both teams and hears both requests"),
                ("remedy", "Explains the transparent next-slot protection.", "written next slot also makes the remedy clear and equal"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=29,
            ),
            _two(
                "A shop sign extended into a shared walkway. Instead of removing only the newest shop's sign, the committee measured every sign on the lane, explained one width rule to all owners, and set the same repair deadline. Owners could show measurement errors before action was taken.",
                "What makes this decision process fair? Give two evidence-based reasons.",
                "The committee measures every sign and applies one width rule and deadline to all owners. It also allows each owner to challenge a measurement error before any penalty or removal.",
                ("equal", "Explains the common measurement, rule, and deadline.", "measures every sign and applies one width rule and deadline to all owners"),
                ("hearing", "Explains the opportunity to correct evidence.", "allows each owner to challenge a measurement error before any penalty or removal"),
                skills=["reading.inference_reason", "writing.reason_answer"],
                min_words=28,
            ),
        ],
    },
    "panchayat-language-relations": {
        "transfer": [
            _two(
                "The reading tent stands between the neem tree and the notice board. A rope path runs from the gate to the tent, while the water point is beyond the board.",
                "Explain between and beyond from the layout, then use both in one accurate sentence.",
                "Between places the tent in the middle of the tree and board, while beyond places the water point farther past the board. The tent is between two landmarks, and the water point is beyond the notice board.",
                ("meanings", "Explains both spatial relations from context.", "Between places the tent in the middle of the tree and board, while beyond places the water point farther past the board"),
                ("sentence", "Uses both prepositions in a complete sentence.", "tent is between two landmarks, and the water point is beyond the notice board"),
                skills=["reading.word_meaning_context", "grammar.prepositions"],
                min_words=34,
            ),
        ],
        "review": [
            _two(
                "A first-aid box hangs above the desk, and a folded stretcher rests beside the cupboard. Visitors walk through the open doorway to reach them.",
                "Interpret above, beside, and through, then write one sentence preserving all three relations.",
                "Above means higher than the desk, beside means next to the cupboard, and through describes movement by way of the doorway. Visitors pass through the doorway to items above the desk and beside the cupboard.",
                ("meanings", "Explains the three relation words from the scene.", "Above means higher than the desk, beside means next to the cupboard, and through describes movement by way of the doorway"),
                ("use", "Uses all three relations accurately.", "pass through the doorway to items above the desk and beside the cupboard"),
                skills=["reading.word_meaning_context", "grammar.prepositions"],
                min_words=34,
            ),
            _two(
                "The painted crossing lies across the road from the clinic. A cycle stand is behind the clinic, and a bench sits near the crossing.",
                "Use the location clues to explain across and behind, then combine them in a clear direction sentence.",
                "Across shows that the crossing is on the opposite side of the road from the clinic, while behind places the cycle stand at the clinic's rear. Cross toward the clinic, then go behind it to reach the stand.",
                ("relations", "Explains across and behind using the landmarks.", "Across shows that the crossing is on the opposite side of the road from the clinic, while behind places the cycle stand at the clinic's rear"),
                ("direction", "Uses the relations in an executable direction.", "Cross toward the clinic, then go behind it to reach the stand"),
                skills=["reading.word_meaning_context", "grammar.prepositions"],
                min_words=36,
            ),
        ],
    },
    "panchayat-past-chronology": {
        "transfer": [
            _one(
                "The clerk posted the revised queue list at noon. The public meeting began at one o'clock.",
                "Join the events to show clearly which action was already complete before the meeting began.",
                "The clerk had posted the revised queue list before the public meeting began at one o'clock.",
                "clerk had posted the revised queue list before the public meeting began",
                description="Uses past perfect for the earlier event and simple past for the later event.",
                skills=["grammar.tense_usage"],
                min_words=15,
            ),
        ],
        "review": [
            _one(
                "Workers measured the broken drain cover on Monday. The council ordered a replacement on Tuesday.",
                "Write one sentence that makes the earlier completed measurement clear.",
                "The workers had measured the broken drain cover before the council ordered a replacement on Tuesday.",
                "workers had measured the broken drain cover before the council ordered a replacement",
                description="Marks the measurement as earlier than the later order.",
                skills=["grammar.tense_usage"],
                min_words=15,
            ),
            _one(
                "Paint on the crossing dried overnight. The guard reopened the lane the next morning.",
                "Combine the events with accurate tense to show why reopening happened later.",
                "The crossing paint had dried overnight before the guard reopened the lane the next morning.",
                "crossing paint had dried overnight before the guard reopened the lane",
                description="Uses the earlier completed action to explain the later reopening.",
                skills=["grammar.tense_usage"],
                min_words=14,
            ),
        ],
    },
    "panchayat-clue-prediction": {
        "transfer": [
            _two(
                "Dark clouds gather above an outdoor book stall. The seller looks up, unfolds a waterproof sheet, and asks a helper to hold one corner near the shelves.",
                "Predict the next supported action and state what the clues do not prove.",
                "The seller will probably cover the books with the waterproof sheet before rain begins. The clues do not prove how long the rain will last or whether every book will stay dry.",
                ("prediction", "Uses multiple clues for the likely next action.", "seller will probably cover the books with the waterproof sheet"),
                ("boundary", "States what remains unknown.", "do not prove how long the rain will last or whether every book will stay dry"),
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
                min_words=29,
            ),
        ],
        "review": [
            _two(
                "A caretaker notices a wet patch spreading below a pipe joint. She closes the nearby valve, places a warning cone, and calls the plumber while holding a replacement washer packet.",
                "What is the most likely next step, and which detail remains uncertain?",
                "The plumber will probably inspect the joint and may replace its washer after the water is isolated. The scene does not prove that the washer is the only cause of the leak.",
                ("next", "Predicts an inspection or washer repair from the clues.", "plumber will probably inspect the joint and may replace its washer"),
                ("limit", "Avoids claiming a cause not yet confirmed.", "does not prove that the washer is the only cause of the leak"),
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
                min_words=29,
            ),
            _two(
                "The notice board has an empty lower panel. A volunteer arrives with a large-print meeting notice, tape, and a ruler, then checks the panel's height beside the ramp.",
                "Predict the next action and explain the limit of that prediction.",
                "The volunteer will probably measure and attach the large-print notice to the lower panel near the ramp. The clues do not show the meeting date or prove who requested the new position.",
                ("action", "Predicts measuring and posting from the available objects.", "measure and attach the large-print notice to the lower panel near the ramp"),
                ("limit", "States two details absent from the clues.", "do not show the meeting date or prove who requested the new position"),
                skills=["reading.paragraph_main_idea", "writing.short_answer"],
                min_words=29,
            ),
        ],
    },
    "panchayat-first-person-letter": {
        "transfer": [
            _two(
                "You are Dev. At a neighbourhood garden meeting, adults accepted your idea for a low tool rack that children can reach. Write to your cousin Nila about the event, your feeling, and why the change matters.",
                "Write a friendly first-person message with a greeting, one developed paragraph, and a correctly punctuated close.",
                "Dear Nila,\n\nYesterday I spoke at our garden meeting and suggested a low rack for children's tools. I felt proud when the group accepted the idea because younger helpers will be able to return tools safely without climbing. I hope you can visit when the rack is ready.\n\nYour cousin,\nDev",
                ("message", "Includes the event, feeling, reason, and invitation in first person.", "I felt proud when the group accepted the idea because younger helpers will be able to return tools safely without climbing"),
                ("format", "Uses a greeting and correctly punctuated friendly close.", "Dear Nila", "Your cousin,\nDev"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=43,
                ordered=True,
            ),
        ],
        "review": [
            _two(
                "You are Sana. The local library added an early Saturday hour after families requested a quieter time for young readers. Write to your friend Isha about the change and invite her to join you.",
                "Create a warm first-person message with a clear reason, complete paragraph, greeting, and close.",
                "Dear Isha,\n\nOur library will now open one hour earlier on Saturdays after families asked for a quieter reading time. I am excited because we can choose books before the room becomes busy. Would you like to meet me there this Saturday?\n\nYour friend,\nSana",
                ("content", "Explains the change, feeling, reason, and invitation.", "I am excited because we can choose books before the room becomes busy. Would you like to meet me there this Saturday?"),
                ("format", "Uses correctly capitalized greeting and friendly close.", "Dear Isha", "Your friend,\nSana"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=41,
                ordered=True,
            ),
            _two(
                "You are Kunal. Workers repaired the uneven footpath near your grandfather's home and added a handrail beside the steep part. Write to him about what you noticed and how the change may help.",
                "Write a respectful friendly message in first person with one connected paragraph and correct punctuation.",
                "Dear Grandpa,\n\nI walked past your lane today and saw that the uneven footpath has been repaired. Workers also added a handrail beside the steep section, so the walk should feel steadier after rain. I am glad the request was heard, and I will visit on Sunday.\n\nWith love,\nKunal",
                ("content", "Reports both changes and explains a likely benefit.", "Workers also added a handrail beside the steep section, so the walk should feel steadier after rain"),
                ("format", "Uses a capitalized greeting and punctuated affectionate close.", "Dear Grandpa", "With love,\nKunal"),
                skills=["grammar.punctuation_capitalization", "writing.friendly_message", "writing.paragraph"],
                interaction="paragraph_text",
                min_words=45,
                ordered=True,
            ),
        ],
    },
    "panchayat-less-words": {
        "transfer": [
            _two(
                "A wireless microphone let the speaker move away from the cable, but a careless grip almost made it fall.",
                "Explain how -less changes wire and care, then use both formed words in context.",
                "Wireless means operating without a wire, while careless means acting without enough care. The wireless microphone needed a careful grip even though no cable was attached.",
                ("formation", "Explains both base words and the without meaning.", "Wireless means operating without a wire, while careless means acting without enough care"),
                ("use", "Uses the formed words accurately in the scene.", "wireless microphone needed a careful grip even though no cable was attached"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=26,
            ),
        ],
        "review": [
            _two(
                "A fearless child does not mean a child who never notices danger; it describes someone who acts without being controlled by fear. A pointless rule has no useful point.",
                "Explain both -less words and use each meaning in a sensible sentence.",
                "Fearless means not controlled by fear, while pointless means without a useful purpose. A fearless speaker can still prepare carefully, and a pointless rule should be reviewed.",
                ("meanings", "Builds both meanings from the base nouns.", "Fearless means not controlled by fear, while pointless means without a useful purpose"),
                ("context", "Uses both words in suitable contexts.", "fearless speaker can still prepare carefully, and a pointless rule should be reviewed"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=26,
            ),
            _two(
                "The hall became noiseless after the machines stopped, but it was not lifeless because people were still reading and working quietly.",
                "Show how -less changes noise and life, and explain why the two words are not interchangeable here.",
                "Noiseless means without noise, while lifeless means without life. The hall can be noiseless yet full of living people, so lifeless would give an entirely wrong meaning.",
                ("formation", "Explains both words from their base nouns.", "Noiseless means without noise, while lifeless means without life"),
                ("contrast", "Explains why only noiseless fits the hall.", "hall can be noiseless yet full of living people, so lifeless would give an entirely wrong meaning"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=27,
            ),
        ],
    },
    "panchayat-bounded-research": {
        "transfer": [
            _two(
                "Packet A, meeting minutes: 'On 4 July, members approved two benches for the east courtyard.' Packet B, dated photograph: two wrapped benches stand beside the east gate on 12 July. Neither source records installation.",
                "Report two supported facts and state the strongest limit on what the packet proves.",
                "The minutes show that two east-courtyard benches were approved on 4 July, and the photograph shows two wrapped benches near the east gate on 12 July. The packet does not prove that the benches were installed or used.",
                ("facts", "Attributes one fact to each source.", "minutes show that two east-courtyard benches were approved on 4 July, and the photograph shows two wrapped benches near the east gate on 12 July"),
                ("limit", "Rejects an unsupported completion claim.", "does not prove that the benches were installed or used"),
                skills=["research.information_selection"],
                min_words=36,
            ),
        ],
        "review": [
            _two(
                "Rain table: Monday 12 mm, Tuesday 0 mm, Wednesday 18 mm. Note: the gauge was read at 8 a.m. each day. The table includes no monthly totals or crop records.",
                "State two exact findings and one conclusion the table cannot support.",
                "Wednesday had the highest listed rainfall at 18 mm, while Tuesday recorded 0 mm at the daily reading. The table cannot show the month's total rainfall or prove any effect on crops.",
                ("findings", "Reports two values with their days.", "Wednesday had the highest listed rainfall at 18 mm, while Tuesday recorded 0 mm"),
                ("boundary", "Rejects claims beyond the table.", "cannot show the month's total rainfall or prove any effect on crops"),
                skills=["research.information_selection"],
                min_words=30,
            ),
            _two(
                "Poster: 'Repair workshop, 20 July, community hall, 10 a.m.' Receipt: twelve tyre patches purchased on 18 July. No attendance sheet or repair log is included.",
                "Combine the supported source facts and state what happened at the workshop only if the packet proves it.",
                "The poster scheduled a repair workshop for 20 July at 10 a.m. in the community hall, and the receipt records twelve tyre patches bought two days earlier. The packet cannot prove who attended or how many repairs were completed.",
                ("facts", "Attributes the event details and purchase correctly.", "poster scheduled a repair workshop for 20 July at 10 a.m. in the community hall, and the receipt records twelve tyre patches bought two days earlier"),
                ("limit", "Rejects unsupported attendance and outcome claims.", "cannot prove who attended or how many repairs were completed"),
                skills=["research.information_selection"],
                min_words=37,
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
    anchors["eng_c5_ch08:transfer:11-14"]["coverage_treatment"] = (
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
    "panchayat-fairness-reasoning-guided-1": {
        "record": "Record all three late arrivals",
    },
    "panchayat-fairness-reasoning-independent-1": {
        "repair": "replace the damaged seedlings",
        "prevention": "play boundary should move away from the garden",
    },
    "panchayat-fairness-reasoning-transfer-2": {
        "recognition": "Recognise each member's documented contribution",
        "boundary": "visible speaker should not receive credit for all shared work",
    },
    "panchayat-fairness-reasoning-review-1": {
        "revision": "Withdraw the blame because location alone did not prove use",
        "followup": "compare later readings before assigning any household responsibility",
    },
    "eng_c5_ch08-assessment-panchayat-fairness-reasoning-4": {
        "hearing": "Hear the people affected, clarify the claim",
        "evidence": "verify relevant evidence",
        "principle": "apply a stated principle",
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
    for item in MANIFEST["chapter_assessment"]["items"]:
        if item["activity_id"] == "eng_c5_ch08-assessment-panchayat-less-words-3":
            item["model_answer"] += " The suffix marks absence."
            item["min_response_words"] = 6


_CONTENT_REPAIRS = {
    "panchayat-dialogue-attribution:guided:3": {
        "model_answer": (
            "The speaker is Meera. She addresses Iqbal. Her request is for him to "
            "show the measurement mark to the committee."
        ),
        "relevance_terms": ["Meera", "Iqbal", "measurement mark"],
    },
    "panchayat-dialogue-attribution:review:3": {
        "model_answer": (
            "The questioner is Rohan, who asks whether the readings were recorded. "
            "The answerer is Mira, who confirms that they were. The word our refers "
            "to the table made by Mira and her group."
        ),
        "relevance_terms": ["Rohan", "Mira", "our"],
    },
    "panchayat-dialogue-attribution:transfer:4": {
        "model_answer": (
            "The problem speaker is Asha. She says the high notice is hard to "
            "read. The response speaker is the clerk. The clerk promises a second "
            "copy beside the ramp that afternoon."
        ),
        "relevance_terms": ["Asha", "high notice", "clerk"],
    },
}


_ATOMIC_REQUIREMENT_REPAIRS = {
    "panchayat-sequence-summary:bridge:1": [
        ("first", "States the first event.", "The complaint was recorded"),
        ("next", "States the next event.", "both neighbours were heard"),
        ("last", "States the final event.", "the boundary stone was measured last"),
    ],
    "panchayat-dialogue-attribution:guided:3": [
        ("speaker", "Identifies the speaker.", "The speaker is Meera"),
        ("listener", "Identifies the person addressed.", "She addresses Iqbal"),
        (
            "request",
            "States what the speaker asks the listener to do.",
            "show the measurement mark to the committee",
        ),
    ],
    "panchayat-dialogue-attribution:review:3": [
        (
            "questioner",
            "Identifies who asks for information.",
            "The questioner is Rohan",
        ),
        ("answerer", "Identifies who answers.", "The answerer is Mira"),
        (
            "reference",
            "Resolves what our refers to.",
            "our refers to the table made by Mira and her group",
        ),
    ],
    "panchayat-dialogue-attribution:guided:4": [
        ("reference", "Resolves the pronoun reference.", "She refers to Rani"),
        ("purpose", "States the purpose of Rani's reply.", "her intention to submit the completed form"),
    ],
    "panchayat-dialogue-attribution-independent-2": [
        ("speaker", "Identifies who states the condition.", "The customer"),
        ("condition", "States the condition attached to payment.", "payment conditional on fixing the loose bolt"),
    ],
    "panchayat-dialogue-attribution-transfer-2": [
        ("speaker", "Identifies who commits to action.", "The worker commits to inspecting the named section"),
        ("reason", "Explains the evidence that makes the commitment specific.", "the resident identifies a specific blockage location"),
    ],
    "panchayat-dialogue-attribution:transfer:4": [
        ("problem_speaker", "Identifies who raises the problem.", "The problem speaker is Asha"),
        ("problem", "States the access problem Asha raises.", "the high notice is hard to read"),
        ("response_speaker", "Identifies who promises action.", "The response speaker is the clerk"),
        ("response", "States the clerk's promised action.", "The clerk promises a second copy beside the ramp that afternoon"),
    ],
    "panchayat-dialogue-attribution:revision_level_2:1": [
        ("reference", "Resolves who He refers to.", "He is Neel"),
        ("evidence", "States the evidence Neel gives.", "his viewing position beside the post as evidence"),
    ],
    "panchayat-language-relations-independent-1": [
        (
            "direction",
            "Uses the direction preposition through.",
            "walked through the gate",
        ),
        (
            "position",
            "Uses the position preposition before.",
            "stood before the chairperson",
        ),
        (
            "surface",
            "Uses the surface preposition on.",
            "placed the letter on the table",
        ),
    ],
    "panchayat-language-relations-independent-2": [
        ("claim", "Defines a claim.", "A claim is what a person says is true"),
        ("evidence", "Defines evidence.", "evidence is information used to test that statement"),
    ],
    "panchayat-language-relations-transfer-1": [
        ("group", "Uses among for the group relationship.", "divided the cost among themselves"),
        ("position", "Uses between for the two-house position.", "the wall stood between both houses"),
    ],
    "panchayat-language-relations-review-1": [
        ("time", "Uses outside for the waiting position.", "waited outside the hearing room"),
        ("movement", "Uses into for movement to the room.", "walked into the room when called"),
    ],
    "panchayat-past-chronology:guided:3": [
        (
            "earlier_event",
            "Identifies copying the complaint as the earlier event.",
            "The clerk copied the complaint first",
        ),
        (
            "verb_form",
            "Names had copied as the verb form that marks the earlier event.",
            "had copied marks the earlier completed past event",
        ),
    ],
    "panchayat-past-chronology-review-2": [
        ("first", "States the first event.", "First the bus departed"),
        ("second", "States the second event.", "then Lina reached the stop"),
    ],
    "panchayat-clue-prediction-independent-2": [
        (
            "supported_action",
            "Names the action directly supported by the clue.",
            "Watering the plant is supported by the dry soil",
        ),
        (
            "prediction",
            "Separates the possible later result from a guaranteed fact.",
            "the plant becoming firmer later is a reasonable prediction, not a guaranteed fact",
        ),
    ],
    "panchayat-less-words:guided:3": [
        ("formed_word", "Forms powerless correctly.", "The torch was powerless"),
        ("sentence_use", "Uses powerless to show the torch could not work.", "could not light the path"),
    ],
    "panchayat-less-words-transfer-2": [
        ("meaning", "Explains the meaning of soundless.", "'Soundless' means without sound"),
        ("alternative", "Gives a natural alternative.", "'silent' is a natural alternative"),
    ],
    "panchayat-less-words:revision_level_1:1": [
        ("base", "Identifies the base noun.", "The base noun is moon"),
        ("meaning", "Explains the formed word.", "moonless means without visible moonlight"),
    ],
    "panchayat-bounded-research-transfer-1": [
        (
            "storage",
            "Reports the supported storage method.",
            "Seeds are stored in labelled dry jars",
        ),
        (
            "record_fields",
            "Reports all fields recorded for each deposit.",
            "each deposit records crop, village, and collection year",
        ),
    ],
    "eng_c5_ch08-assessment-panchayat-sequence-summary-3": [
        ("claim", "States the initial claim.", "Students make accusations"),
        ("evidence", "States what the recording proves.", "the recording shows a table failure"),
        ("response", "States the group's response.", "the group responds by repairing the leg and rebuilding together"),
    ],
    "eng_c5_ch08-assessment-panchayat-language-relations-4": [
        ("relationship_strategy", "States the preposition strategy.", "Name the relationship before choosing a preposition"),
        ("context_strategy", "States the vocabulary-in-context strategy.", "use surrounding clues to test a vocabulary meaning in the whole sentence"),
    ],
    "eng_c5_ch08-assessment-panchayat-past-chronology-3": [
        ("earlier", "Uses past perfect for the earlier event.", "The chef had measured the flour first"),
        ("later", "Uses simple past for the later event.", "then she mixed the dough"),
    ],
    "eng_c5_ch08-assessment-panchayat-past-chronology-4": [
        ("form", "States the past-perfect form.", "Use had plus the past participle for the earlier completed event"),
        ("purpose", "States the simple-past purpose.", "use simple past for the later reference event"),
    ],
    "eng_c5_ch08-assessment-panchayat-bounded-research-3": [
        ("material", "Names the material used.", "fallen palm leaves"),
        (
            "preparation",
            "States how long the material is dried.",
            "dries fallen palm leaves for three days",
        ),
        (
            "product",
            "Names the product made from the material.",
            "weaves them into small baskets",
        ),
        (
            "boundary",
            "Preserves the live-leaf boundary.",
            "without cutting live leaves",
        ),
    ],
}


_SELECTED_OPTION_REPAIRS = {
    "panchayat-fairness-reasoning-co": {
        "prompt": (
            "Which option makes the fairest decision and cites the strongest "
            "evidence?"
        ),
    },
    "panchayat-language-relations-guided-1": {
        "prompt": (
            "Which option fills the place, starting-point, and ending-point "
            "relationships?"
        ),
    },
    "panchayat-past-chronology-guided-1": {
        "prompt": "Which option explains the time relationship in 'had opened'?",
    },
    "panchayat-past-chronology-guided-2": {
        "prompt": "Which option puts the two events in the order expressed?",
    },
    "panchayat-clue-prediction-co": {
        "prompt": "Which prediction is supported by both visible clues?",
        "options": [
            (
                "The dog may have left through the open gate because muddy "
                "footprints lead there and it is absent from its shelter."
            ),
            "The dog must still be in its shelter because footprints prove nothing.",
            "A visitor carried the dog away because the feed bowl is empty.",
            "The dog certainly left the area forever through the open gate.",
        ],
        "accepted_answers": [
            (
                "The dog may have left through the open gate because muddy "
                "footprints lead there and it is absent from its shelter."
            )
        ],
    },
    "panchayat-first-person-letter-co": {
        "prompt": (
            "Which sentence is a clear first-person response to both parts of the "
            "decision?"
        ),
        "options": [
            "The council made a decision about a farmer and a player.",
            "I am writing about a different field that was not discussed.",
            (
                "I accept the replacement plan and would like to know when the "
                "boundary will be moved."
            ),
            "I reject the decision without mentioning either remedy.",
        ],
        "accepted_answers": [
            (
                "I accept the replacement plan and would like to know when the "
                "boundary will be moved."
            )
        ],
    },
    "panchayat-less-words-co": {
        "passage": (
            "A rule with no fairness needs a natural English word, but not every "
            "noun forms a standard word with -less."
        ),
        "prompt": (
            "Which option rejects the nonstandard form fairless and gives the "
            "natural alternative?"
        ),
        "options": [
            "fairless, because every noun accepts -less",
            "unfair; fairless is not a standard English word",
            "refair, because re- means no fairness",
            "fairly, because an adverb means without fairness",
        ],
        "accepted_answers": [
            "unfair; fairless is not a standard English word"
        ],
    },
    "panchayat-less-words-guided-2": {
        "prompt": (
            "Which option explains fearless without claiming the child takes "
            "unsafe risks?"
        ),
    },
    "panchayat-bounded-research-co": {
        "prompt": "Which option reports two supported facts about the service?",
    },
    "panchayat-bounded-research-guided-1": {
        "prompt": (
            "Which option reports the volunteer role and its safety boundary?"
        ),
    },
    "eng_c5_ch08-assessment-panchayat-bounded-research-1": {
        "prompt": (
            "Which option reports the schedule and requirement without inventing "
            "a service?"
        ),
    },
    "eng_c5_ch08-assessment-panchayat-less-words-2": {
        "prompt": "Which option avoids the unsupported inference?",
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
        activity.update(repair)

    for activity_id, requirements in _ATOMIC_REQUIREMENT_REPAIRS.items():
        _set_atomic_requirements(activities[activity_id], requirements)

    levels = {level["level_id"]: level for level in MANIFEST["levels"]}
    levels["panchayat-clue-prediction"]["connect"]["teaching_block"] = (
        "A written scene card can supply visible clues when no image is shown. "
        "Separate what those clues prove from what they only suggest before "
        "making a prediction."
    )

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
