---
created: 2026-07-12
project: zidd
ecosystem: full-stack
tags: [school-prep, placement, implementation-plan, tdd]
---

# School Placement Rebuild Implementation Plan

> **Superseded 2026-07-13:** This placement-only plan is retained as history. Execute `2026-07-13-school-prep-canonical-rebuild.md` instead.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Every behavior change starts with a failing test.

**Goal:** Deliver an authored, adaptive, evidence-backed English placement flow for Classes 2-5 that accurately routes learners to target curriculum or a personalized Readiness Path without granting mastery.

**Architecture:** Preserve canonical `/school`, generic School session persistence, answer-claim idempotency, profile lineage, and the shared readiness engine. Replace the current global fallback selector and shallow bank with eight authored diagnostic tracks per target class, per-track boundary state, strict evaluator evidence, deterministic terminal rules, and an immutable recap-ready report.

**Tech Stack:** FastAPI, Pydantic v2, PostgreSQL/Supabase repository layer, pytest, Next.js/TypeScript, Playwright over the dedicated School CDP profile.

Design: `../../../../validation/school-prep-placement-design-2026-07-12.md`

## File Map

- `app/content/school_rebuild_placement_bank.py`: placement content models, approved tracks, public projection, and class 2-5 authored bank.
- `app/content/school_rebuild_placement_validation.py`: hard content gate for tracks, bands, variants, localization, rubrics, and no-key-leak projection.
- `app/services/school_rebuild_placement.py`: canonical envelope, track selector, stage transitions, evidence resolution, and public response.
- `app/services/school_v3_placement.py`: remove from canonical runtime after compatibility tests prove no active import; shared readiness remains under `school_core`.
- `app/api/school_rebuild_routes.py`: placement evaluator orchestration, atomic answer persistence, resume, abandon, and structured errors.
- `app/services/school_rebuild_report.py`: terminal status, conservative class boundary, private recap handoff, and learner/parent report projection.
- `tests/hardening/test_school_rebuild_phase_2_placement_contract.py`: canonical engine/API behavior.
- `tests/hardening/test_school_rebuild_placement_content_contract.py`: full Class 2-5 bank quality and leakage gate.
- `tests/integration/test_school_placement_postgres.py`: real PostgreSQL CAS/idempotency/lineage/report proof.
- `src/services/schoolRebuild.ts`: exact frontend placement types and endpoints.
- `src/app/school/placement/page.tsx` and `src/app/school/placement/[sessionId]/page.tsx`: landing and one-item-per-screen activity.
- `tests/browser/school-placement.spec.ts`: multi-learner live browser flows.

## Task 1: Lock The Authored Placement Content Contract

**Files:** create `app/content/school_rebuild_placement_validation.py`; modify `app/content/school_rebuild_placement_bank.py`; create `tests/hardening/test_school_rebuild_placement_content_contract.py`.

- [ ] Write failing tests asserting Classes 2-5 each expose exactly eight snapshot tracks; each item has one primary skill; every reachable source band has two unused variants; all three teaching languages have learner-safe support copy; open items have strict rubrics; every item ID is unique; and public projection recursively excludes answer keys, accepted answers, rubric/model answers, and hidden scoring fields.
- [ ] Run `.venv/bin/pytest -q tests/hardening/test_school_rebuild_placement_content_contract.py` and verify failures describe the missing Class 2, Class 4/5 Stage 2, localization, primary-skill, and variant contracts.
- [ ] Replace the tuple-only item model with `PlacementTrack`, `PlacementBand`, and `SchoolPlacementBankItem` models containing `primary_skill_id`, telemetry-only tags, source band, evaluation mode, localization, rubric reference, misconception tags, and approval metadata.
- [ ] Author the required Class 2-5 diagnostic tracks. Remove leaked/mistagged prompts and the Class 3 target-class typo identified by audit. Do not import seed chapter items or create a fallback prompt.
- [ ] Implement `validate_placement_bank()` and fail module load for any missing approved track/band/variant/localization/rubric.
- [ ] Re-run the focused tests and the source-map/taxonomy tests; require green before Task 2.

## Task 2: Replace The Global Stage Machine With Per-Track Boundaries

**Files:** modify `app/services/school_rebuild_placement.py`; modify compatibility serialization in `app/services/school_v3_runtime.py`; test `tests/hardening/test_school_rebuild_phase_2_placement_contract.py`.

- [ ] Write failing pure-engine tests for: eight-pass target-ready; mixed snapshot selecting only failed/ambiguous tracks; downward band selection after miss; upward narrowing after lower-band pass; Stage 3 only on contradiction/insufficient evidence; no unrelated fallback; all-weak budget ending below-target or insufficient with an explicit terminal reason; and duplicate item application as a no-op.
- [ ] Add failing serialization round-trip tests covering track plans, boundaries, unresolved reasons, pending queues, timing metadata, and engine-version rejection/migration.
- [ ] Run the focused tests and confirm current behavior fails because it copies results across skills, falls back to unrelated items, and can complete on bank exhaustion.
- [ ] Implement immutable `PlacementTrackState`, `PlacementAttemptEvidence`, and `PlacementSessionState` under the canonical module. Keep one primary scored skill per item.
- [ ] Implement deterministic `pass/fail/ambiguous/unscorable` classification and per-track binary band selection under the 8/18 budget.
- [ ] Finalize `target_ready`, `below_target`, and `insufficient_evidence` exactly as the design specifies; call shared `apply_placement_ready_seed` only when all required tracks are resolved ready.
- [ ] Remove canonical imports of `school_v3_placement`; retain a compatibility re-export only if remaining archived tests require it. Extend the AST guard so no second readiness formula appears.
- [ ] Run pure engine, shared-core, and runtime serialization suites green.

## Task 3: Integrate Deterministic And Strict Open-Answer Evaluation

**Files:** modify `app/content/school_rebuild_placement_bank.py`, `app/services/school_rebuild_placement.py`, and `app/api/school_rebuild_routes.py`; tests in the Phase 2 contract.

- [ ] Write failing tests proving MCQ/fill/exact items grade deterministically, real writing items invoke the strict rubric evaluator, a Hindi response cannot certify an English-production item, inflated model scores cannot override missing criteria, invalid schema/provider failure does not mutate state or evidence, and local evaluation has no timeout.
- [ ] Run the focused tests and capture the current binary `accepted_answers` failures.
- [ ] Reuse the existing claim-heartbeat and strict School rubric contract. Convert evaluator output to one primary-skill placement evidence record; backend thresholds remain authoritative.
- [ ] On evaluator failure, fail the claim and return retriable `503` without consuming the item. Do not classify it as incorrect.
- [ ] Return learner-safe feedback and support language while excluding hidden evaluator fields.
- [ ] Run evaluator, placement, no-key-leak, and atomicity tests green.

## Task 4: Make Placement Persistence And Reports Authoritative

**Files:** modify `app/api/school_rebuild_routes.py`, `app/services/school_rebuild_report.py`, `app/db/repo.py` only if the existing atomic boundary lacks a required field; create `tests/integration/test_school_placement_postgres.py`.

- [ ] Write failing API tests for Classes 2-5 start/resume, exact active-profile lineage, same-answer replay, different-answer conflict, stale CAS, unauthorized access, explicit abandon, terminal report idempotency, and no readiness/report creation on insufficient or abandoned paths.
- [ ] Write failing report tests for conservative `evaluated_class_no`, Foundation naming, evidence-backed weak/unresolved tracks, misconception tags, language-support signals, and private recap-handoff data.
- [ ] Add `POST /school/placement/{session_id}/abandon`; it terminalizes only an active session and never unlocks curriculum.
- [ ] Persist answer event, session CAS, replay response, readiness seeds, and optional terminal report in one repository transaction. Reuse existing tables unless a verified missing field requires an additive migration.
- [ ] Ensure `GET /school/state` maps active, insufficient, below-target, target-ready, and abandoned placement states to exactly one backend-owned next action.
- [ ] Run focused hardening and disposable PostgreSQL tests green, including concurrent submit and report replay.

## Task 5: Connect Placement Output To A Non-Generic Readiness Path

**Files:** modify `app/services/school_rebuild_recap.py` and `app/services/school_rebuild_report.py`; tests `test_school_rebuild_phase_3_report_recap_contract.py` and placement contract.

- [ ] Write failing tests that every below-target terminal fixture builds a path solely from approved modules mapped to confirmed weak or unresolved track IDs; unresolved tracks begin with diagnostic activities; source-class ordering is preserved; raw IDs/labels never become prompts; and missing authored content fails closed.
- [ ] Delete the generic `Write the answer for <focus>` fallback and label-as-identity path construction.
- [ ] Build recap plans from private placement handoff fields and taxonomy prerequisite edges. Confirmed gaps start teaching modules; unresolved tracks start short diagnostics; non-blocking residuals become watchlist entries.
- [ ] Run report, recap, no-fallback, and curriculum-lock suites green.

## Task 6: Build The Routed Placement Learner Experience

**Files:** modify `src/services/schoolRebuild.ts`, `src/app/school/placement/page.tsx`; create `src/app/school/placement/[sessionId]/page.tsx` and focused components under `src/components/school/placement/`; add frontend contract tests.

- [ ] Write failing frontend tests for exact backend response drift, one primary action, one activity per screen, persisted resume, stage transition copy, pending evaluation, retriable failure, abandon confirmation, no client-derived readiness, and no hidden key/rubric rendering.
- [ ] Implement the placement landing and session route using the existing Career visual language while preserving backend-owned state. Localize task instructions from the response; do not translate English evidence passages.
- [ ] Show calm progress as `Snapshot`, `Focused check`, and `Confirming`; never expose raw skill IDs, class-placement certainty before terminal state, or false success.
- [ ] Run Node contract tests, TypeScript, ESLint, production build, and `git diff --check`.

## Task 7: Live Multi-Learner Browser And Database Gate

**Files:** create `tests/browser/school-placement.spec.ts`; create `validation/school-prep-placement-qa-2026-07-12.md` and database evidence report after execution.

- [ ] Use only the dedicated School Chrome profile on CDP 9225 and `[SCHOOL_QA_ACCOUNT]`; never query or modify Ryuk.
- [ ] Reset only that QA user's School placement/report/answer rows between scenarios while preserving onboarding unless a scenario explicitly tests it.
- [ ] Run real browser journeys for Class 2 strong, Class 3 mixed/weak, Class 4 contradictory, Class 5 broadly weak/insufficient, Hinglish support, evaluator retry, refresh/resume, duplicate submit, abandon, unauthorized, and no-key-leak.
- [ ] For every journey, capture visible question/answer/feedback/stage/report logs, exact mobile/tablet/desktop layout evidence, request evidence with secrets removed, and read-only Supabase rows matching the browser journey.
- [ ] Run an independent spec review and code-quality review. Fix every Critical and Important finding, rerun affected browser scenarios, then run the full hardening suite.
- [ ] Mark placement accepted only when the implementation, browser transcript, DB rows, report, and recap handoff agree exactly.

## Completion Boundary

This plan completes the staged placement phase only. It does not claim the full
School Prep goal complete. The next accepted phase is personalized Readiness Path
execution and bounded masterclass pause/resume, followed by curriculum tutor,
learner growth, complete pedagogically approved Class 2-5 content, and final
multi-user E2E.
