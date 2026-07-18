# Class 5 deep-chapter manifests

Create one author-reviewed input per chapter:

`app/content/school_rebuild_manifests/english/class_5/eng_c5_chNN.json`

These files are authoring inputs, not runtime chapters. The compiler always
emits `approval_status: "draft"`; review and release approval happen later.

## Top-level contract

```json
{
  "schema_version": "school-class5-deep-manifest-v1",
  "chapter": {
    "chapter_id": "eng_c5_chNN",
    "chapter_no": 2,
    "title": "Chapter title",
    "book_title": "Santoor",
    "unit_title": "Unit title",
    "source_url": "https://ncert.nic.in/textbook/pdf/eesa1NN.pdf",
    "source_note": "NCERT structural alignment only. All learner-facing content is Zidd-authored.",
    "content_version": "2026-07-15.1",
    "certification_version": "2026-07-15.1",
    "authorship": {
      "zidd_authored_original": true,
      "textbook_body_or_questions_copied": false,
      "source_analysis_reference": "reviewed structural exercise matrix"
    }
  },
  "source_anchors": [],
  "levels": [],
  "chapter_assessment": {
    "items_per_attempt": 16,
    "pass_score": 0.8,
    "max_attempts": 2,
    "bank_item_count": 32,
    "items": [],
    "strands": []
  }
}
```

`source_anchors` uses `LiveSourceAnchor`: `anchor_id`, `section_label`,
`page_start`, `page_end`, official NCERT `source_url`,
`coverage_treatment`, and `required_for_chapter_certification`.

## Level contract

Every intended runtime level must have exactly one manifest entry. The
manifest may add, remove, or replace levels from a shallow input chapter; it
is the complete authority for the compiled draft.

```json
{
  "level_id": "chapter_specific_level_id",
  "title": "Learner-visible level title",
  "focus": "Specific skill focus",
  "outcome": "Observable outcome the learner must demonstrate",
  "skill_ids": ["closed.taxonomy.skill"],
  "episode_kind": "comprehension_studio",
  "source_anchor_ids": ["eng_c5_chNN:section:pages"],
  "connect": {
    "teaching_block": "Explicit Zidd-authored connection teaching",
    "passage": "Explicit Zidd-authored example",
    "prompt": "Explicit continue prompt"
  },
  "co_construct": {},
  "guided_variants": [{}, {}],
  "independent_variants": [{}, {}],
  "transfer_variants": [{}, {}],
  "review_variants": [{}, {}],
  "misconception_clusters": [],
  "support_checks": {
    "bridge": {},
    "masterclass": {},
    "revision_level_1": {},
    "revision_level_2": {},
    "revision_level_3": {}
  }
}
```

An activity is either `kind: "selected_option"` with explicit literal
`options` and `accepted_answers`, or `kind: "open_response"` with explicit
rubric criteria, matching concept slots, forbidden phrases, relevance terms,
model answer, response length, and interaction type. Every activity carries
its own `activity_id`, learner-facing copy, and genuinely assessed `skill_ids`.

Selected-option activity:

```json
{
  "kind": "selected_option",
  "activity_id": "chapter-level-guided-a",
  "teaching_block": "Explicit strategy for this exact task",
  "passage": "Original Zidd-authored stimulus",
  "prompt": "Specific question",
  "skill_ids": ["receptive.or.recognition.skill"],
  "options": ["literal correct option", "plausible distractor"],
  "accepted_answers": ["literal correct option"]
}
```

Selected options may not claim writing, speaking, oral, or production skills.
Those require a constructed response.

Open activity:

```json
{
  "kind": "open_response",
  "activity_id": "chapter-level-independent-a",
  "teaching_block": "Explicit task-specific instruction",
  "passage": "Original Zidd-authored stimulus",
  "prompt": "Specific constructed-response question",
  "skill_ids": ["writing.reason_answer"],
  "interaction_type": "paragraph_text",
  "rubric_criteria": [
    {
      "id": "claim",
      "description": "States the required claim",
      "required": true,
      "min_quality": 0.7
    }
  ],
  "concept_slots": [
    {
      "id": "claim",
      "description": "States the required claim",
      "any_of": ["task-specific semantic phrase", "valid alternative"]
    }
  ],
  "forbidden_phrases": ["known copied exemplar phrase"],
  "min_response_words": 12,
  "relevance_terms": ["task term one", "task term two"],
  "model_answer": "Hidden original reference answer used by the evaluator",
  "pass_score": 0.8
}
```

Each misconception cluster requires `cluster_id`, `skill_ids`, a concrete
`misconception`, a concrete `remediation`, and `support_check_ids`. Together,
the clusters must cover every level skill and reference every support check.

```json
{
  "cluster_id": "event-order-confusion",
  "skill_ids": ["reading.sequence"],
  "misconception": "Concrete description of the learner error",
  "remediation": "Concrete instructional response, not a retry prompt",
  "support_check_ids": [
    "level-bridge",
    "level-masterclass",
    "level-revision-1",
    "level-revision-2",
    "level-revision-3"
  ]
}
```

`chapter_assessment.items` contains the complete 32-item authored bank using
the same selected-option/open-response shapes shown above; `activity_id`
becomes the runtime `item_id`. Each assessment strand requires `strand_id`, disjoint `skill_ids`,
`minimum_items`, exact `evidence_forms` (`selected_option` and/or
`constructed_response`), and `remediation_level_ids`. The blueprint must match
the existing assessment bank exactly, and every assessed skill must resolve to
authored remediation.

```json
{
  "strand_id": "narrative-comprehension",
  "skill_ids": ["reading.sequence", "reading.inference_reason"],
  "minimum_items": 6,
  "evidence_forms": ["selected_option", "constructed_response"],
  "remediation_level_ids": ["chapter_sequence_level"]
}
```

Compile only after authoring is complete:

```bash
python scripts/build_school_class5_deep_chapter.py \
  --manifest app/content/school_rebuild_manifests/english/class_5/eng_c5_chNN.json \
  --output /tmp/eng_c5_chNN.deep.json
```

Pass `--chapter` only when an existing chapter should be checked for matching
chapter identity before it is replaced. Omit it to create a missing chapter.
