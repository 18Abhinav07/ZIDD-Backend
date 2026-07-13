# School Prep Phase 2 Placement Plan

> **Superseded 2026-07-13:** This historical pilot plan is not executable authority. Use `docs/superpowers/plans/2026-07-13-school-prep-canonical-rebuild.md`.

## Goal

Build the first real placement slice for the rebuilt `/school` surface.

This phase does not build recap, curriculum teaching, or masterclasses. It proves the diagnostic contract:

1. Read the active versioned school profile.
2. Start or resume a backend-owned placement session.
3. Serve authored, context-bearing placement questions.
4. Score answers deterministically where possible.
5. Advance from broad snapshot to targeted diagnostic from evidence.
6. Persist placement state and expose it through `/school/state`.
7. Never unlock target curriculum or mark mastery from placement alone.

## Scope

First slice:

- Subject: English.
- Target class: Class 3.
- Prerequisite band: Class 2 English readiness.
- Supported teaching languages in metadata: `en`, `hi`, `hi_en`.
- Content source: net-new placement bank, not the generated `school_v3_blueprints` seed prompts.

Unsupported class behavior:

- Class 2, 4, and 5 profiles may complete onboarding.
- Starting placement for unsupported classes returns a clear `placement_slice_not_ready` error until their item banks exist.
- `/school/state` should not pretend class work is available.

## Content Contract

Create a small authored placement bank for Class 3:

- 8 snapshot items.
- 8 targeted diagnostic items.
- 4 confirmatory items.
- Every item includes:
  - `item_id`
  - `subject_id`
  - `target_class_no`
  - `source_class_no`
  - `stage`: `snapshot`, `targeted_diagnostic`, or `confirmatory`
  - `skill_ids`
  - `learner_skill_label`
  - `prompt`
  - optional `passage`
  - `item_type`
  - deterministic `answer_key` and `accepted_answers`
  - `misconception_tags`

Public responses include prompt, passage, options, stage, and learner label only. They must not expose answer keys, accepted answers, model answers, rubrics, or hidden thresholds.

## Backend API

Add rebuilt routes under `/school`, not `/school/v3`:

- `POST /school/placement/start`
  - Requires active school profile.
  - Uses profile target class, subject, preferred language, and difficulty signals.
  - Does not accept class/language from the client.
  - Starts or resumes one active placement session.

- `GET /school/placement/{session_id}`
  - Resumes a placement session owned by the user.

- `POST /school/placement/{session_id}/answer`
  - Accepts `item_id`, `answer`, and optional client idempotency key later.
  - Rejects answers for any item other than the backend-selected next item.
  - Duplicate item answer returns the current state without double scoring.

## State API Integration

`GET /school/state` must consult active/completed placement sessions:

- No active/completed placement: `start_placement`.
- Active placement: `resume_placement`, URL `/school/placement`.
- Completed placement, target-ready: `view_placement_report` first, not curriculum.
- Insufficient evidence: `resume_placement` or `view_placement_report` depending final status.
- Below-target: `view_placement_report`, then recap in Phase 3.

Phase 2 may report `placement_status=below_target` or `target_ready`, but must keep `unlock_state=locked` until Phase 3/4 explicitly implements recap/curriculum unlock rules.

## Placement Algorithm

Reuse the verified readiness core and the existing staged placement state shape, but do not use the old `/school/v3` route.

Item selection:

- Snapshot stage:
  - Prefer profile prior difficulty signals first.
  - Cover high-signal Class 2 prerequisite skills and Class 3 readiness skills.
  - Max 8 items.

- Targeted diagnostic:
  - Select items for skills missed or low-confidence in snapshot.
  - Max 18 total items.

- Confirmatory:
  - Select only when the learner shows enough recovery or contradictory evidence.
  - Confirms readiness seed only; no mastery.

Scoring:

- Deterministic grading for MCQ/fill/short exact items.
- Placement can set readiness seed for confirmed-ready skills.
- Placement cannot set mastered status.

## Tests First

Create `tests/hardening/test_school_rebuild_phase_2_placement_contract.py` before implementation.

Required RED tests:

1. Starting placement without a school profile returns `409 school_profile_required`.
2. Starting placement uses the saved Class 3 Hinglish profile and returns a snapshot item from the authored bank.
3. Public placement item response does not leak answer keys, accepted answers, rubrics, or thresholds.
4. `/school/state` changes from `start_placement` to `resume_placement` after start.
5. Answering the expected snapshot item persists progress and returns the next item.
6. Answering any non-next item returns `409 unexpected_placement_item`.
7. Re-answering the same item is idempotent and does not increment answered count.
8. A weak snapshot answer routes the session into targeted diagnostic after enough snapshot coverage.

## Browser QA Gate

Use `[SCHOOL_QA_ACCOUNT]` only.

QA path:

1. Reset only that user's school rows.
2. Onboard as Class 3 English with Hinglish support.
3. Open `/school`.
4. Start placement.
5. Record first 3 questions and verify they are understandable and based on visible context.
6. Intentionally answer one item incorrectly.
7. Verify the next questions target the failed skill.
8. Reload `/school` and verify it resumes placement, not onboarding or fake curriculum.

## Exit Criteria

- Backend focused tests pass.
- Frontend type/lint/surface checks pass.
- Browser QA transcript proves onboarding -> placement start -> answer -> resume.
- No answer key leakage in public responses.
- The report explicitly states that recap/curriculum remain unimplemented until later phases.
