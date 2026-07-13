---
created: 2026-07-13
project: zidd
ecosystem: full-stack
tags: [school-prep, implementation-plan, curriculum, adaptive-learning, browser-qa]
status: approved-for-execution
---

# School Prep Canonical Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Every task requires an implementation review and an adversarial product/pedagogy review before the next phase begins.

**Goal:** Replace the beta School Prep internals behind the canonical `/school` product with a complete NCERT-aligned Class 2-5 English tutor that performs bounded placement, compiles evidence-specific readiness work, teaches the real target curriculum, branches into finite support, and maintains one auditable learner projection across sessions.

**Architecture:** Preserve the current canonical `/school` API, generic `school_sessions`, profile lineage, idempotent answer claims, and approved Career-cohesive UI shell. Replace parallel V1/V2/V3/rebuild content and learning logic with one release registry, one banded standards graph, one transactional evidence projector, deterministic journey policies, provider-neutral semantic evaluation, and approved original content. The backend remains the only authority for next action, unlocks, readiness, mastery, support caps, reports, and entitlements.

**Tech Stack:** FastAPI, Pydantic v2, PostgreSQL/Supabase, SQLAlchemy text queries, Python dataclasses, Next.js 14 App Router, TypeScript, React, Framer Motion, Lucide, Playwright plus live Chrome CDP browser QA on ports 3001/8088.

Backlinks: [[docs/school-prep-rebuild-architecture-contract]] [[validation/school-prep-current-product-audit]]

---

Path convention: backend paths are relative to `BUILD/Zidd-Backend`; frontend paths are relative to `BUILD/Zidd-Frontend`. Commands state their working directory explicitly.

## Execution Rules

1. Work only in `BUILD/Zidd-Backend` and `BUILD/Zidd-Frontend`, both on `school-prep`.
2. The worktrees are dirty and contain user/agent work. Never reset, checkout, or delete unrelated changes. Before every task, record `git status --short` and limit the review to owned files.
3. Do not create `/school/v4`, `/school/v5`, or another learner-facing version. Extend the canonical `/school` contract.
4. Do not use Gemini. Local development semantic evaluation uses Qwen through the provider-neutral evaluator interface and has no short model timeout.
5. Tests prove invariants; authenticated browser journeys prove the product. A large passing test count alone is not a phase gate.
6. Every answer-changing transaction commits the answer request, session transition, evidence row, event row, projection update, and any report change atomically.
7. Never expose answer keys, accepted answers, hidden rubrics, scoring thresholds, planner state, or model answers in public responses.
8. Internal QA may serve `agent_qa_approved` content only behind a non-production flag. Controlled family beta requires `product_owner_approved`; under the approved risk decision, the agent performs and records the review and may promote through this gate under the product owner's explicit delegation. School-partnership or teacher-reviewed claims require `qualified_teacher_approved`.

## Shared Commands

Backend focused test command:

```bash
cd BUILD/Zidd-Backend
./.venv/bin/pytest -q tests/hardening/test_school_canonical_*.py tests/integration/test_school_canonical_*.py
```

Backend development server:

```bash
cd BUILD/Zidd-Backend
./.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8088
```

Frontend validation and development server:

```bash
cd BUILD/Zidd-Frontend
npm run test:school-rebuild-surface
npx tsc --noEmit
npm run dev:school-prep
```

Dedicated authenticated School browser profile:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9225 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-Zidd-SchoolPrep" \
  http://localhost:3001/auth/login
```

Use the signed-in `theopenassets@gmail.com` profile. Never modify or test with the Ryuk account. Browser evidence must come from real navigation and interaction through port 3001; API calls are allowed only for setup diagnostics and database assertions, not as a substitute for the learner journey.

Migration execution invariant: every new migration in this plan must also be appended to `scripts/apply_migrations.py` in dependency order, mirrored in `app/db/schema.sql`, asserted by `app/db/schema_guard.py`, recorded with its file hash in `school_migration_markers`, and exercised against both an empty schema and an upgraded representative copy. A migration task is incomplete until all five surfaces pass.

## Canonical File Map

### Backend authority retained

- `app/api/school_rebuild_routes.py`: current mounted `/school` router. It remains mounted while endpoints are migrated to focused canonical services; no second router is mounted.
- `app/services/school_rebuild_state.py`: backend next-action authority; move to `app/services/school/state.py` only after compatibility imports and tests exist.
- `app/services/school_core/readiness.py`: single readiness formula; migrate to `app/services/school/readiness.py` with a compatibility re-export.
- `app/db/repo.py`, `app/storage/pg_store.py`: repository transaction boundary.
- `school_profile_versions`, `school_sessions`, `school_answer_requests`, `school_placement_reports`: retained persistence foundations.

### Backend canonical modules added

- `app/content/school/release_schema.py`: immutable curriculum release and structural module types.
- `app/content/school/releases/english_cbse_2026_27.json`: verified release manifest.
- `app/content/school/release_loader.py`: fail-hard release loading and source-hash verification.
- `app/content/school/standards.py`: closed banded standards registry and prerequisite graph.
- `app/content/school/content_schema.py`: lesson, activity, misconception, rubric, and assessment contracts.
- `app/content/school/content_loader.py`: approved-content loader.
- `app/content/school/placement_bank.py`: eight-track/class multi-band diagnostic bank.
- `app/services/school/evidence.py`: immutable evidence records and public-safe serialization.
- `app/services/school/projector.py`: the only learner projection transition.
- `app/services/school/evaluator.py`: deterministic and strict semantic evaluators.
- `app/services/school/evaluation_jobs.py`: pending semantic-evaluation leases and recovery.
- `app/services/school/journey.py`: immutable plan compiler and versioning.
- `app/services/school/placement.py`: bounded staged placement.
- `app/services/school/readiness_path.py`: focused prerequisite plan compiler.
- `app/services/school/teaching.py`: deterministic next-activity policy.
- `app/services/school/support.py`: linked support/masterclass policy and finite caps.
- `app/services/school/reports.py`: live learner/parent reports from committed projection.
- `app/services/school/language.py`: scaffolding meta-signal, isolated from certification.

### Frontend retained and extended

- `src/app/school/**`: canonical routes.
- `src/services/schoolRebuild.ts`: rename internally to canonical School types only after all call sites compile; public service methods remain stable during migration.
- `src/components/learning/LearningWorkspace.tsx`, `JourneyMap.tsx`, `LearningSkeletons.tsx`: shared Career-cohesive shell.
- `src/components/school/**`: adapt to backend activity discriminators; do not replace the approved visual system.
- `public/school-prep-visual-aid.html`: screenshot/reference oracle, never production runtime.

### Archived after cutover only

- `app/api/school_routes.py`.
- `app/services/school_v2_*`, `app/services/school_v3_*`, superseded `school_rebuild_*` services.
- `app/content/data/school/**`, `app/content/school_v3_blueprints/**`, generated seed corpus, and stale rebuild content that fails the canonical gold gate.
- `/subjects`, `/subjects/v2`, `/subjects/v3` remain redirects until the final release window ends.

## Phase 0: Authority And Curriculum Release Lock

### Task 0.0: Create a recoverable dirty-worktree baseline

**Files:**
- Backend create: `docs/qa/school-prep-baseline-backend.md`
- Frontend create: `docs/qa/school-prep-baseline-frontend.md`

- [x] Record backend/frontend branch names, HEAD SHAs, `git status --short`, untracked School files, and modified shared files before runtime edits.
- [x] Save binary-safe patch manifests with `git diff --binary` and a separate untracked-file inventory outside Git under `/tmp/zidd-school-baseline-<head>/`; record its SHA-256 manifest in the QA documents.
- [x] Classify each dirty path as School-owned, Career-owned/unrelated, or shared. Do not stage Career-owned/unrelated paths. Shared-file edits must use hunk-level review and task-owned staging.
- [x] Create a School-only baseline checkpoint commit only from already coherent School-owned files after reviewing its staged diff. If mixed shared-file hunks cannot be separated safely, retain the external patch manifest and do not force a commit. The verified external manifest was used because shared files contain mixed Career/School hunks.
- [x] Verify restoration by applying the patch manifest to a temporary clean checkout/worktree and comparing the School-owned file hashes. Do not reset either live worktree.

### Task 0.1: Freeze the approved architecture and supersede stale plans

**Files:**
- Modify: `docs/school-prep-rebuild-architecture-contract.md`
- Modify: `docs/school-prep-phase-0-1-implementation-plan.md`
- Modify: `docs/school-prep-phase-2-placement-plan.md`
- Modify: `docs/superpowers/plans/2026-07-12-school-placement-rebuild.md`

- [x] Mark the architecture contract `status: approved`, including approval date and product owner.
- [x] Add a two-line supersession notice to every older plan linking to this file. Do not delete older evidence.
- [x] Run `rg -n 'status:|superseded' docs/school-prep*.md docs/superpowers/plans/*.md` and verify exactly one plan is approved for execution.

### Task 0.2: Define and verify the immutable 2026-27 release

**Files:**
- Create: `app/content/school/__init__.py`
- Create: `app/content/school/release_schema.py`
- Create: `app/content/school/releases/english_cbse_2026_27.json`
- Create: `app/content/school/release_loader.py`
- Create: `scripts/verify_school_release.py`
- Create: `tests/hardening/test_school_canonical_release_contract.py`

- [x] Write failing tests that require `curriculum_release_id`, board, subject, class, academic year, book title/code/ISBN, official URLs, SHA-256 source hashes, edition/reprint metadata, effective dates, ordered units, lesson modules, picture-reading modules, self-assessments, listening/speaking structures, and verification evidence.
- [x] Assert the four immutable book identities: Class 2 `Mridang/bemr1`, Class 3 `Santoor/cesa1`, Class 4 `Santoor/desa1`, Class 5 `Santoor/eesa1`.
- [x] Assert the manifest represents structural modules, not only the 47 numbered/title modules.
- [x] Implement strict Pydantic models with `extra="forbid"`; reject duplicate order positions, duplicate module IDs, missing hashes, unsupported classes, and retired releases used as current.
- [x] Implement `load_current_release(subject_id="english", class_no=N)` and trusted-manifest `verify_release_sources(curriculum_release_id)`; source verification compares persisted hashes and metadata, never downloads at API boot.
- [x] Populate the release manifest from the verified official source map and local official PDF hashes. Store only source metadata, declared pedagogical structures, and verification evidence; do not store textbook body text.
- [ ] Run:

```bash
./.venv/bin/pytest -q tests/hardening/test_school_canonical_release_contract.py
./.venv/bin/python scripts/verify_school_release.py --release english_cbse_2026_27 --source-dir /tmp/zidd-ncert-release-sources
```

Expected: four classes verified, zero manifest errors, and a deterministic release digest.

### Task 0.3: Establish minimal canonical compatibility contracts

**Files:**
- Create: `app/content/school/standards.py`
- Create: `app/content/school/content_schema.py`
- Create: `app/services/school/evaluator_contract.py`
- Create: `tests/hardening/test_school_canonical_compatibility_contracts.py`

- [ ] Define the final `CompetencyStandardRef` identity fields and registry interface without authoring the full graph yet. Adapt the existing locked English taxonomy into these objects so Phase 0 runtime no longer imports `school_v3_taxonomy`.
- [ ] Define the final source-map module reference, `OpenAnswerRubric`, rubric criterion, and strict evaluator-result DTOs with `extra="forbid"`. Adapt current approved content/evaluator payloads at the boundary so Phase 0 runtime no longer imports V3 schema/evaluator types.
- [ ] Keep these modules as the canonical files expanded by Phases 1-2; those phases modify them and must not create replacement contracts.
- [ ] Add compatibility tests proving current canonical `/school` responses are unchanged while all V3 runtime imports are removed.

### Task 0.4: Lock one runtime and route authority

**Files:**
- Create: `app/services/school/authority.py`
- Create: `scripts/audit_school_runtime_authority.py`
- Create: `tests/hardening/test_school_canonical_authority_contract.py`
- Modify: `app/main.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `app/content/school_rebuild_content.py`
- Modify: `app/content/school_rebuild_placement_validation.py`
- Modify: `app/services/school_rebuild_curriculum.py`
- Modify: `app/services/school_rebuild_placement_evaluator.py`

- [ ] Write a failing test that inspects `app.routes` and requires one mounted `/school/state`, one handler per canonical path/method, and no mounted V1/V2/V3 School router.
- [ ] Add a static import audit that rejects new runtime imports from `school_v2_*`, `school_v3_*`, `app/content/data/school`, or generated seed loaders outside compatibility/archive tests.
- [ ] Record every canonical endpoint and its owning service in `CANONICAL_SCHOOL_AUTHORITY`; route registration fails if duplicated.
- [ ] Remove the canonical runtime's remaining `school_v3_content`, `school_v3_taxonomy`, and V3 evaluator imports by adapting the Phase 0 release/standard compatibility interfaces. Keep old modules importable only for historical tests until Phase 7.
- [ ] Keep `school_rebuild_routes.router` mounted for compatibility, but change its internal imports task-by-task to canonical modules. Do not mount `school_routes.router`.
- [ ] Run:

```bash
./.venv/bin/pytest -q tests/hardening/test_school_canonical_authority_contract.py
./.venv/bin/python scripts/audit_school_runtime_authority.py
```

Expected: one canonical router, zero forbidden active imports.

### Task 0.5: Prove migration compatibility before changing data

**Files:**
- Create: `app/db/migrations/2026-07-13-001-school-release-authority.sql`
- Create: `scripts/preflight_school_migrations.py`
- Modify: `app/db/schema.sql`
- Modify: `app/db/schema_guard.py`
- Modify: `scripts/apply_migrations.py`
- Create: `tests/integration/test_school_canonical_release_migration.py`

- [ ] Write the integration test against PostgreSQL before the migration. It must fail because `school_curriculum_releases` and release lineage columns do not exist.
- [ ] Add one immutable `school_curriculum_releases` row per subject/class release with `curriculum_release_id TEXT PRIMARY KEY` (for example `english_cbse_2026_27_c2_r1`), manifest JSON, release digest, status, effective/retired dates, and uniqueness on `(board_id, subject_id, class_no, academic_year, release_digest)`. Reject updates to manifest/digest through a database trigger; corrections create a new release ID.
- [ ] Add nullable `curriculum_release_id`, `taxonomy_version`, and `certification_epoch` to `school_sessions` and `school_placement_reports`; do not make them non-null until lineage backfill is validated. The release FK is many sessions/reports to one subject/class release row.
- [ ] Add nullable `coach_avatar_id` and `coach_palette_id` to `school_profile_versions`; onboarding activation fills both in one transaction. Existing profiles receive a deterministic one-time backfill based on profile-version ID, after which the stored values are authoritative.
- [ ] Backfill only current canonical `api_version='rebuild'` sessions whose subject/class maps unambiguously to the approved release. Keep ambiguous historical rows nullable and non-authoritative.
- [ ] Preserve the existing partial unique index:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_sessions_one_active_flow
ON school_sessions(user_id, flow_type, subject_id, class_no)
WHERE status IN ('active', 'paused_for_masterclass');
```

- [ ] Treat all existing July 9-12 migration SQL as immutable history. Append new migrations to the explicit dependency-ordered `DEFAULT_MIGRATIONS` list; do not infer order from filenames.
- [ ] Extend `school_migration_markers` with the applied file SHA-256 and applied timestamp for canonical School migrations. Refuse to rerun a migration name whose stored hash differs from the checked-in file.
- [ ] Run a preflight that records counts and IDs for active profiles/sessions/reports, verifies predecessor tables/constraints, and aborts before SQL if lineage is ambiguous. Persist the preflight output with migration QA evidence.
- [ ] Run both an empty-schema migration test and an upgraded-copy test containing representative existing profiles, active sessions, linked sessions, reports, and drafts. Then apply through `scripts/apply_migrations.py`, rerun to prove idempotency, and query schema metadata for columns, FKs, partial unique index, RLS, and revoked client grants.

### Task 0.6: Lock onboarding, state authority, and persisted visual identity

**Files:**
- Modify: `app/services/school_rebuild_profile.py`
- Modify: `app/services/school_rebuild_state.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `src/components/school/onboarding/SchoolOnboardingWizard.tsx`
- Modify: `src/components/school/setup/ClassSubjectStep.tsx`
- Modify: `src/lib/schoolTheme.ts`
- Create: `tests/hardening/test_school_canonical_onboarding_state.py`
- Create: `tests/schoolVisualIdentity.test.ts`

- [ ] Preserve versioned onboarding fields: learner name, school, board, target class, subjects, preferred teaching language, English comfort, learner/parent goals, and prior difficulty signals.
- [ ] Verify the UI has a real class/subject/board selection step sourced from the backend catalog; unsupported combinations show an honest unavailable state and cannot start placement.
- [ ] Keep `GET /school/state` as the sole next-action authority for onboarding, placement, report, readiness path, curriculum, support, review, and reports; the frontend must not infer unlocks from local storage.
- [ ] Persist `coach_avatar_id` and `coach_palette_id` on the activated `school_profile_versions` row for class home/reports. Every immutable journey plan also snapshots its coach identity; a linked support/masterclass may choose a new coach once at session creation, stores it in that session plan, and never reselects it on render.
- [ ] Use the persisted avatar palette for surface accents. Do not derive identity independently from route strings such as class number, report type, or session ID once the persisted identity exists.
- [ ] Add a browser baseline capture of all current canonical School routes before core behavior changes so later visual regressions are attributable.

**Phase 0 gate:** release verifier clean; one mounted School authority; migration applies twice; focused tests green; canonical state/onboarding/visual identity verified; no core learner behavior changed.

## Phase 1: Banded Standards And Transactional Evidence Authority

### Task 1.1: Create the closed banded standards graph

**Files:**
- Modify: `app/content/school/standards.py`
- Create: `app/content/school/standards/english_2_5.json`
- Create: `scripts/validate_school_standards.py`
- Create: `tests/hardening/test_school_canonical_standards_contract.py`

- [ ] Define standard identity as `(subject_id, skill_id, proficiency_band, taxonomy_version, certification_epoch)`; `proficiency_band` is required and ranges 1-5 for the first release.
- [ ] Cover listening/oral comprehension, speaking, reading/viewing, vocabulary, grammar/use, writing, and module knowledge.
- [ ] Give every standard `class_min`, `class_max`, `prerequisite_standard_ids`, supported activity modes, certification language, blocker tags, and misconception clusters.
- [ ] Add a cycle detector and prerequisite-closure test. Reject unknown prerequisites, duplicate identities, broad generic `reading`/`grammar` leaf skills, and a standard whose certifying modes cannot be authored.
- [ ] Assert Class 2 and Class 5 standard IDs never collide even when the skill label is shared.

### Task 1.2: Make the shared readiness module the only formula

**Files:**
- Create: `app/services/school/readiness.py`
- Modify: `app/services/school_core/readiness.py`
- Modify: `app/services/school_v2_readiness.py`
- Modify: `app/services/school_rebuild_learning.py`
- Create: `scripts/check_single_school_readiness_formula.py`
- Create: `tests/hardening/test_school_canonical_readiness_contract.py`

- [ ] First audit the existing shared module for subject/class literals. The audit must reject `class_no == 5`, `subject_id == "english"`, hardcoded skill IDs, or route concerns inside readiness math.
- [ ] Move the behaviorally identical formula into `app/services/school/readiness.py`; make old modules compatibility re-exports only.
- [ ] Preserve exact alphas: bridge `.15`, guided `.25`, placement `.30`, independent `.45`, transfer `.50`, review `.40`, chapter `.55`; effective alpha is base alpha times evaluator confidence; the first attempt sets the relevant readiness directly.
- [ ] Preserve thresholds and gates: pass `.80`, ready `.80`, mastery `.90`; ready requires two independent passes or placement seed; mastery requires three independent passes, one transfer pass, no blockers, and support dependency below `.25` in the last five attempts.
- [ ] Preserve review intervals `3/7`, doubling to `30`, failed review to `1`; later failure must be able to lower readiness and mastery classification.
- [ ] Add `review_due` and `next_review_at` to the canonical state. Classification checks a missed due review before mastered/ready; a due standard cannot unlock new dependent work until a passing review restores it.
- [ ] Persist blockers until a later independent qualifying attempt demonstrates the blocked criterion. Guided, bridge, scaffolded, mismatched-language, or unrelated independent success cannot clear an active blocker.
- [ ] Normalize current `guided_check` to canonical `guided` and masterclass activities to their real pedagogical attempt type (`guided`, `bridge`, `independent_check`, or `transfer_check`); `masterclass` is a flow/source label, never a new readiness alpha.
- [ ] Delete `_ATTEMPT_ALPHA` and all projection writes from `school_rebuild_learning.py`; it may become a compatibility facade but cannot calculate readiness or set mastery to `1.0`.
- [ ] Add an AST check that detects inline as well as named EMA arithmetic and fails if another School module defines readiness movement or writes mastery with `GREATEST`/monotonic semantics.

### Task 1.3: Add immutable School evidence, events, and projection tables

**Files:**
- Create: `app/db/migrations/2026-07-13-002-school-banded-evidence.sql`
- Modify: `app/db/schema.sql`
- Modify: `app/db/schema_guard.py`
- Modify: `scripts/apply_migrations.py`
- Modify: `app/db/repo.py`
- Modify: `app/storage/pg_store.py`
- Modify: `tests/conftest.py`
- Create: `tests/integration/test_school_canonical_evidence_migration.py`

- [ ] Add `answer_request_id UUID NOT NULL DEFAULT gen_random_uuid()` plus a unique constraint to `school_answer_requests` and backfill existing rows. Add `school_attempts`: `attempt_id UUID` primary key; unique `(session_id, activity_id)` and unique `answer_request_id`; FKs to session and answer request; user, profile, flow, release/taxonomy/certification, nullable plan ID/version/node, content item/version, rubric/evaluator versions, attempt type, score/confidence, support/language/blocker/criteria payloads, scored and telemetry standard arrays, answer excerpt/encrypted-retention reference, source key, and timestamp.
- [ ] Content remains immutable versioned files, so `content_item_id`/`content_version` are validated against the loaded release rather than a fabricated relational content FK. `plan_id` is stored nullable without an FK in migration `002`; migration `005` validates existing non-null IDs then adds the journey-plan FK after that authority exists.
- [ ] Add `school_attempt_standard_evidence`: one row per explicitly scored standard, FK to `school_attempts`, full standard identity, score/confidence/blockers, and composite primary key `(attempt_id, subject_id, skill_id, proficiency_band, taxonomy_version, certification_epoch)`. Telemetry standards never receive rows here.
- [ ] Add `school_session_events` with immutable event ID and unique `(session_id, sequence_no)`, session/plan versions, event type, visible/public payload, private decision payload, causation/attempt IDs, and timestamp.
- [ ] Add banded `school_skill_profiles` keyed by `(user_id, subject_id, skill_id, proficiency_band, taxonomy_version, certification_epoch)`, storing practice/certified readiness, pass counters, blockers, recent support flags, review schedule, projection version, and `last_attempt_id` FK.
- [ ] Add `school_projection_checkpoints` for replay diagnostics, not as an alternate source of truth.
- [ ] Enable RLS and revoke `anon`, `authenticated`, and `PUBLIC`; repository/service role remains the only writer.
- [ ] Add repository methods to append evidence/events and get one projection under row lock. Mirror exact behavior in `tests/conftest.py` without weakening concurrency checks.

### Task 1.4: Project every answer inside the existing atomic transaction

**Files:**
- Create: `app/services/school/evidence.py`
- Create: `app/services/school/projector.py`
- Modify: `app/db/repo.py:persist_school_answer_attempt`
- Modify: `app/storage/pg_store.py:persist_school_answer_attempt`
- Modify: `tests/conftest.py:persist_school_answer_attempt`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `app/services/school_rebuild_curriculum.py`
- Modify: `app/services/school_rebuild_masterclass.py`
- Modify: `app/services/school_rebuild_placement.py`
- Modify: `app/services/school_rebuild_recap.py`
- Create: `tests/integration/test_school_canonical_atomic_projection.py`
- Create: `tests/hardening/test_school_canonical_projection_replay.py`

- [ ] Define `SchoolAttemptEvidence` with full standard identity, immutable evaluator result, `scored_standard_ids`, separate telemetry standard IDs, attempt type, support level, language evidence, blockers, hints, criteria, release, and version fields. Only scored standards enter the projector.
- [ ] Implement a pure `project_attempt(previous, evidence) -> SkillReadinessState` by adapting the evidence into the single readiness module.
- [ ] Extend `persist_school_answer_attempt` to lock session and projections, append evidence/event, upsert the projection, update session/report, and complete the answer request before one commit.
- [ ] Force rollback when any projection write fails; assert no completed answer request, session advance, orphan evidence, or learning event remains.
- [ ] Implement replay ordered by `(school_attempts.created_at, attempt_id, standard identity)` and compare every field with the persisted projection.
- [ ] Add tests proving Class 2/Class 5 evidence isolation, duplicate-submit idempotency, late failure regression, and identical multi-standard evidence applied independently to each explicit `scored_standard_id`; telemetry standards receive no projection update.
- [ ] Migrate curriculum, masterclass, placement, and recap answer call sites to build canonical evidence before persistence. Remove every post-commit `SchoolLearningProfileService` projection call and warning-swallow path; no School flow may advance and project in separate transactions.

### Task 1.5: Migrate legacy School history as hints, never certification

**Files:**
- Create: `scripts/migrate_legacy_school_evidence.py`
- Create: `tests/integration/test_school_canonical_legacy_hint_migration.py`

- [ ] Read legacy `school_skill_mastery`, `school_results`, and School-domain generic learning profiles.
- [ ] Map only unambiguous rows to non-projecting `historical_hint` prior metadata. It may prioritize placement ordering but is unscorable: it changes neither readiness value nor pass counter and never enters the evidence projector.
- [ ] Never create placement seeds, ready, mastered, independent passes, or transfer passes from legacy rows.
- [ ] Make the migration idempotent through a deterministic source event key and produce a reconciliation report.

### Task 1.6: Authenticated projection and reload smoke

**Files:**
- Create: `docs/qa/school-phase-1-browser-smoke.md`

- [ ] In the dedicated School Chrome profile, complete one existing deterministic School activity, reload before and after submission, and verify the visible session never advances without the corresponding projection version.
- [ ] Query the answer claim, event, evidence, projection, and session rows after the browser action; record IDs and prove they share one committed transition.
- [ ] Inject a projection failure in a disposable test environment and confirm the browser receives a recoverable error while session position and answer claim remain uncompleted.

**Phase 1 gate:** event replay exactly reproduces every projection; answer and projection commit together; evidence bands do not collide; later failures regress; static formula guard passes; real Supabase migration evidence and authenticated browser smoke are captured.

## Phase 2: Gold Journey Slice

### Task 2.0: Enforce pre-model entitlement and child-data boundaries

**Files:**
- Create: `app/services/school/privacy.py`
- Create: `app/services/school/entitlements.py`
- Create: `app/db/migrations/2026-07-13-003-school-entitlement-consumption.sql`
- Create: `scripts/grant_school_qa_entitlement.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `app/db/schema.sql`
- Modify: `app/db/schema_guard.py`
- Modify: `scripts/apply_migrations.py`
- Modify: `src/services/schoolRebuild.ts`
- Create: `tests/hardening/test_school_canonical_prelaunch_boundaries.py`
- Create: `tests/integration/test_school_canonical_demo_entitlement.py`

- [ ] Add an internal-QA release channel guard; agent-approved gold content is inaccessible outside explicit local/test/internal QA environments.
- [ ] Enforce the free boundary before session creation: onboarding, placement, full placement report, and one demo lesson total are free; readiness path, ongoing curriculum, support/masterclass, longitudinal reports, and scheduled reviews require family or school entitlement.
- [ ] Add `school_entitlements` with entitlement ID, user, source `family_subscription|school_sponsor|qa_grant`, status, subject/class scope, starts/expires/revoked timestamps, external billing/sponsor reference, and audit metadata. `SchoolEntitlementService` resolves active time/scope and never trusts frontend state.
- [ ] Add a non-production-only service-role script that grants the `theopenassets@gmail.com` user a scoped QA entitlement by resolving its user ID. Production refuses `qa_grant`; expiry/revocation takes effect on the next backend state/start check.
- [ ] Add `school_entitlement_consumptions` with user, benefit type, curriculum release, idempotency key, optional session, state `reserved|consumed|released`, and timestamps; enforce one consumed/reserved `school_demo_lesson` per learner across the initial English release.
- [ ] Reserve the demo atomically with curriculum session creation, consume it when the first learner-visible demo activity is served, and release an unserved reservation on failed creation/expiry. Reload and duplicate starts reuse the same reservation; changing class/subject cannot mint another demo.
- [ ] Define `build_school_evaluator_context()` so later evaluator work can include only the current approved item/rubric, compact active learner evidence, language policy, and submitted answer. Exclude unrestricted transcripts, unrelated profile fields, parent prose, and hidden cross-domain memory.
- [ ] Disable or contractually bound provider prompt/output retention for production child data. Local QA logs redact raw child answers by default; telemetry stores derived status, latency, tokens, and error class.
- [ ] Add authorization tests for cross-user sessions/reports/evidence and verify that no browser response exposes hidden content.

### Task 2.1: Lock the canonical content and rubric schema

**Files:**
- Modify: `app/content/school/content_schema.py`
- Create: `app/content/school/content_loader.py`
- Create: `app/content/school/review_registry.json`
- Create: `scripts/validate_school_content.py`
- Create: `scripts/audit_school_content_semantics.py`
- Create: `tests/hardening/test_school_canonical_content_schema.py`

- [ ] Define private `ChapterCoverageMap` records that map every official source-module requirement to authored outcomes, teaching blocks, activities, and assessments; coverage maps never enter public learner payloads.
- [ ] Define `MediaAssetRef` with asset ID, hashed object-storage/CDN URL, SHA-256, MIME type, byte size, dimensions or duration, alt text, transcript/captions where applicable, fallback asset/text, provenance/rights evidence, and content version. Validators reject missing hashes, inaccessible media metadata, unsupported MIME, mutable URLs, missing alt/transcript, or absent fallback.
- [ ] Define activity discriminators: `teach`, `worked_example`, `mcq`, `multi_select`, `sequence`, `match`, `classify`, `fill_blank`, `short_exact`, `short_open`, `reason_open`, `summary_open`, `picture_reading`, `hotspot`, `listen_respond`, `read_aloud`, `speak_respond`, `role_play`, `guided_write`, `drawing_offline_action`, `game`, and non-certifying `reflection`.
- [ ] Define a strict open-answer rubric before content authoring: schema version, item ID, full standard IDs, score, confidence, detected language, criteria `{id, met, quality, evidence_quote}`, misconception tags, blockers, `needs_human_review`, and learner feedback. Use `extra="forbid"`.
- [ ] Define misconception clusters with at least four bridge items and two distinct reteach strategies.
- [ ] Give each activity cognitive-load band, expected duration, modality requirements/fallback, withdrawal rule, passage-length/readability band, language-scaffold variants, and a verifiable follow-up for drawing/game/offline actions.
- [ ] Implement approval statuses `draft`, `agent_qa_approved`, `product_owner_approved`, `qualified_teacher_approved`. Internal QA may serve agent-approved content behind a non-production flag; controlled family beta requires product-owner approval under the delegated review decision; school claims require qualified-teacher approval.
- [ ] Implement the gold gate: 5-7 meaningful outcomes/chapter; at least 6 semantically unique guided and 6 independent items/outcome; 3 transfer items/outcome; 2 review items/certifying standard; 4 bridge items/misconception; 2 reteach strategies/misconception; 20+ chapter-test items.
- [ ] Detect normalized duplicate prompts, answer-template duplication, option rotation, passage reuse, rubric-ID drift, ungradable open prompts, missing modalities, brittle exact matching for constructed responses, and high similarity to source textbook prose. Similarity failures block approval and require original rewriting; the tool does not store or serve textbook bodies.

### Task 2.2: Author one complete target chapter and prerequisite closure

**Files:**
- Create: `app/content/school/chapters/english/class_5/<gold-chapter>.json`
- Create: `app/content/school/prerequisites/english/<gold-standard>.json`
- Modify: `app/content/school/review_registry.json`
- Create: `tests/hardening/test_school_canonical_gold_slice_content.py`

- [ ] Select one Class 5 chapter only after its official module structure and prerequisite closure are represented in the release/standards graph.
- [ ] Author original Zidd passages, examples, picture prompts, listening scripts, speaking prompts, teaching explanations, exercises, rubrics, chapter checks, and feedback. Do not copy NCERT body text.
- [ ] Meet the full gold gate for the chapter and every prerequisite unit needed by the Class 5->2/3/4/5 controlled journeys.
- [ ] Review every item for factual correctness, child-safe language, English difficulty, answer-key correctness, rubric evidence traceability, bilingual scaffold quality, and semantic uniqueness; record `agent_qa_approved` during internal QA and promote to `product_owner_approved` only under the product owner's explicit delegated family-beta decision. Never convert this into a teacher-reviewed or school-partnership claim.
- [ ] Run the validator and require zero structural or semantic issues before the loader can serve the slice.

### Task 2.2A: Author the final Class 5 gold diagnostic bank

**Files:**
- Create: `app/content/school/placement_bank.py`
- Create: `scripts/validate_school_placement_bank.py`
- Create: `app/content/school/placement/english/class_5.json`
- Create: `tests/hardening/test_school_canonical_gold_placement_bank.py`

- [ ] Author exactly eight final Class 5 diagnostic tracks, one primary standard family each, covering the blocking prerequisite clusters required by the gold journey.
- [ ] Author at least two semantically distinct variants at every reachable Class 2, 3, 4, and 5 band for each track used by the controlled Class 5->2/3/4/5 journeys.
- [ ] Use the final placement-bank schema and validator; Phase 3 may add target Classes 2-4 but cannot rewrite the Class 5 bank contract or engine.
- [ ] Self-grade deterministic items, challenge semantic rubrics, verify comprehensibility in English/Hindi/Hinglish instructions, and require zero answer-key leakage.

### Task 2.3: Implement provider-neutral deterministic and semantic evaluation

**Files:**
- Create: `app/services/school/evaluator.py`
- Create: `app/services/school/evaluation_jobs.py`
- Create: `app/db/migrations/2026-07-13-004-school-evaluation-jobs.sql`
- Modify: `app/db/schema.sql`
- Modify: `app/db/schema_guard.py`
- Modify: `scripts/apply_migrations.py`
- Modify: `app/ai/local.py`
- Create: `tests/hardening/test_school_canonical_evaluator_contract.py`
- Create: `tests/integration/test_school_canonical_evaluation_jobs.py`

- [ ] Deterministically grade MCQ, multi-select, sequence, match, fill-blank, and short-exact items with approved normalization and alternatives.
- [ ] Semantic evaluation accepts only the strict rubric JSON. Reject unknown criteria, fabricated evidence quotes, score/criterion inconsistency, wrong item/standard IDs, and extra fields.
- [ ] Enforce English certification language. Hindi/Hinglish mismatch blocks certified evidence but remains valid practice evidence.
- [ ] Persist `evaluation_pending` before worker execution. Claim/acknowledge in under one second; use a 120-second lease renewed every 30 seconds; offer leave/continue-later after 180 seconds; terminally mark unscorable after two provider failures or ten minutes.
- [ ] Transaction A atomically claims `(session_id, activity_id)`, stores the immutable answer hash/body under the child-data policy, creates one unique evaluation job, records `evaluation_pending`, and returns the pending response without advancing the session.
- [ ] Transaction B locks the answer claim, job, session snapshot, and affected projections; validates claim token, plan version, activity reservation, and non-terminal state; then calls `persist_school_answer_attempt` to append final evidence/events, project readiness, advance session/report, complete the request/job, and commit once.
- [ ] Add uniqueness on answer request/job, lease owner/version, terminal state, and final evidence source key. Tests cover two workers, stale lease reclaim, rollback, duplicate finalization, terminal provider failure, and late valid result discard.
- [ ] Local Qwen has no short model timeout. Hosted mode switches to pending after eight seconds. One repair/retry uses the same immutable answer/rubric. Late results for terminal claims are discarded by claim token and version.
- [ ] Track calls/tokens/latency/fallback by flow and enforce budgets: placement 3 semantic calls, readiness module 2, chapter 8; 2,500 input and 700 output tokens per evaluator request.

### Task 2.4: Compile immutable learner-specific journey plans

**Files:**
- Create: `app/services/school/journey.py`
- Create: `app/services/school/teaching.py`
- Create: `app/db/migrations/2026-07-13-005-school-journey-plans.sql`
- Modify: `app/db/schema.sql`
- Modify: `app/db/schema_guard.py`
- Modify: `scripts/apply_migrations.py`
- Create: `tests/hardening/test_school_canonical_journey_compiler.py`

- [ ] Compile `SchoolJourneyPlan` from release, profile version, placement report, projection snapshot version, entitlement, language preference, and approved content versions.
- [ ] Add `school_journey_plans` with plan ID, user/profile/release/taxonomy/certification lineage, flow, subject/class, monotonically increasing version, status, superseded version, evidence watermark, active node, reason, digest, and timestamps. Enforce one active plan per `(user_id, profile_version_id, subject_id, flow_type)` with a partial unique index.
- [ ] Add `school_plan_content_reservations` keyed by learner/plan/version/content ID with state `reserved|served|consumed|released`, node ID, and served timestamp; add `school_content_exposures` so released content cannot be immediately repeated after recompilation.
- [ ] Add plan/session FKs and compare-and-set supersession at completed node boundaries. Session JSON stores only a public cursor/projection of the authoritative plan.
- [ ] Reserve activity IDs atomically so reload/duplicate submit cannot change the next item. Completion consumes the reservation; supersession/abandon releases unused reservations while preserving served exposure history.
- [ ] Select deterministic teaching progression: orientation -> explicit teaching -> worked example -> guided practice -> independent check -> transfer -> chapter check -> scheduled review.
- [ ] Use difficulty and activity-mode variation from authored banks; LLM may naturalize short feedback but cannot select standards, content, answer keys, or next state.

### Task 2.5: Implement the narrow final placement, support, and target-overlay contracts

**Files:**
- Create: `app/services/school/placement.py`
- Create: `app/services/school/readiness_path.py`
- Create: `app/services/school/support.py`
- Modify: `app/services/school/journey.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `src/services/schoolRebuild.ts`
- Modify: `src/app/school/support/[sessionId]/page.tsx`
- Modify: `src/components/school/support/SchoolSupportActivity.tsx`
- Create: `tests/hardening/test_school_canonical_gold_flow_contract.py`

- [ ] Implement the final staged placement state machine and report contract against the gold Class 5 track bank and its authored prerequisite bands. Phase 3 expands bank coverage; it does not replace this engine.
- [ ] Implement the final readiness-path compiler against the gold prerequisite closure, including early microdiagnostics, watchlist, deviation note, immutable plan versions, and finite revision caps. Phase 4 expands content/strategies; it does not create a second compiler.
- [ ] Implement the final support/masterclass state machine for the gold chapter: linked sessions, pause, resume, abandon-consuming-cap, two interruptions, third-trigger support plan, and executable terminal support session.
- [ ] Implement the complete support lifecycle now: `POST /school/support/start`, `GET /school/support/{session_id}`, `POST /school/support/{session_id}/answer`, and `POST /school/support/{session_id}/abandon`, plus matching frontend service methods and the existing support route. Phase 4 expands strategies/caps but does not add a missing transport contract.
- [ ] Implement the final target overlay for the gold chapter so target-ready and below-target learners receive different valid plans without omitting source coverage. Phase 5 generalizes overlay inputs and reporting.
- [ ] Route every placement/readiness/support/curriculum attempt through the Phase 1 transaction/projector.

### Task 2.6: Extend the approved teaching UI with real activity renderers

**Files:**
- Modify: `src/services/schoolRebuild.ts`
- Modify: `src/components/school/tutor/SchoolActivityRenderer.tsx`
- Modify: `src/components/school/tutor/SchoolTutorWorkspace.tsx`
- Modify: `src/components/school/tutor/SchoolProgressRail.tsx`
- Modify: `src/components/learning/LearningWorkspace.tsx`
- Modify: `src/app/school/session/[sessionId]/page.tsx`
- Create: `tests/schoolActivityRenderer.test.tsx`

- [ ] Add an exhaustive TypeScript discriminated union matching backend public activities; `assertNever` fails compilation for an unrendered type.
- [ ] Render selection, ordering, matching, picture, listening, speaking, writing, and open-response interactions without exposing hidden fields.
- [ ] Preserve Career typography/layout, persisted avatar/palette, one primary action, skeleton loading, calm feedback, keyboard interaction, ARIA status, and responsive geometry.
- [ ] Show `Reviewing` for pending evaluation; reload polls the same claim and cannot resubmit. At 180 seconds show Leave and continue later without marking failure.
- [ ] Keep microphone denied/interrupted/unavailable states explicit and non-shaming; unavailable speaking evidence becomes `not_assessed`.

### Task 2.7: Browser-prove the complete gold learning loop

**Files:**
- Create: `docs/qa/school-gold-slice-browser-qa.md`
- Modify: focused Playwright configuration only if repeatable regression capture needs it.

- [ ] Start backend 8088 and frontend 3001, attach to the existing School Chrome CDP profile on 9225, and authenticate as `theopenassets@gmail.com`.
- [ ] Complete a target-ready journey and a below-target journey through the UI, including placement/report, one readiness activity when applicable, target chapter teaching, independent check, transfer, chapter check, and report.
- [ ] Run repeated weak/support, bilingual, mic-denied, provider-delayed, reload-during-evaluation, duplicate-submit, unauthorized, and no-key-leak variants.
- [ ] At `390x844`, `768x1024`, and `1440x900`, capture every canonical surface and compare with `public/school-prep-visual-aid.html`; require no overflow, overlap, client-only progress, console error, spinner-only loading, or hidden primary action.
- [ ] Run real Android Chrome phone/tablet and real iOS/iPadOS Safari media/input checks at this gold-slice gate, including touch, audio, microphone, keyboard, safe area, interrupted input, and pending-evaluation reload. Record device/OS/browser versions.
- [ ] After every critical action, query session, answer request, event, evidence, projection, plan version, and report lineage. Record IDs and screenshots in the QA document.

**Phase 2 gate:** real browser learners finish both gold journeys; weak answers branch correctly; no false advancement; reload works at every state; all committed evidence reconciles.

## Phase 3: Multi-Band Placement

### Task 3.1: Author the complete diagnostic bank

**Files:**
- Modify: `app/content/school/placement_bank.py`
- Create: `app/content/school/placement/english/class_2.json`
- Create: `app/content/school/placement/english/class_3.json`
- Create: `app/content/school/placement/english/class_4.json`
- Modify: `app/content/school/placement/english/class_5.json`
- Modify: `scripts/validate_school_placement_bank.py`
- Create: `tests/hardening/test_school_canonical_placement_bank.py`

- [ ] Define exactly eight tracks per target class, one primary standard per track, with two semantically distinct variants at every reachable band.
- [ ] Include all lower bands required to distinguish Class 5 readiness at Classes 5, 4, 3, and 2; do not merely tag target items with lower class numbers.
- [ ] Validate deterministic answers/rubrics, discriminative difficulty, accessible language, and no public answer-key fields.

### Task 3.2: Implement bounded staged placement and server timing

**Files:**
- Modify: `app/services/school/placement.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `app/services/school_rebuild_report.py` or replace with `app/services/school/reports.py`
- Create: `app/db/migrations/2026-07-13-006-school-placement-timing.sql`
- Modify: `app/db/schema.sql`
- Modify: `app/db/schema_guard.py`
- Modify: `scripts/apply_migrations.py`
- Create: `tests/hardening/test_school_canonical_placement_engine.py`
- Create: `tests/integration/test_school_canonical_placement_timing.py`

- [ ] Stage 1 snapshot: breadth-first, max eight items or 240 seconds.
- [ ] Stage 2 targeted diagnostic: binary/bounded search over lower bands for weak/ambiguous tracks, max 300 seconds; by overall item 14 it must hand off if confirmation is needed.
- [ ] Stage 3 confirmatory: only weak/downward/contradictory tracks, max four reserved items or 180 seconds.
- [ ] Enforce 18 total items. If more than four unlock-critical tracks require confirmation, return `insufficient_evidence`.
- [ ] Persist per-track `highest_passed_band`, `lowest_failed_band`, tested variants, targeted/confirmation count, contradiction state, and confidence. Select the midpoint untested authored band between bounds; without a pass lower bound move toward the lowest prerequisite anchor, and without a failed upper bound move upward.
- [ ] Schedule blocking prerequisites first, then ambiguity, prior difficulty signal, and stable track order. One track cannot consume more than three targeted/confirmatory items while another blocking track has no targeted evidence.
- [ ] Classify pass as score >= `.80`, confidence >= `.75`, no blocker; fail as score < `.60`, confidence >= `.70`; ambiguous for `.60-.80`, low confidence, skip, or mismatch; provider/modality failure is unscorable.
- [ ] Allow a clean Stage 1 pass only when score and confidence are both >= `.85`; seed certified readiness at `.80` but never mastery.
- [ ] Compute stage elapsed from persisted server timestamps/heartbeats; never trust client elapsed time. Duplicate/concurrent answers cannot double-count or erase elapsed time.
- [ ] Output `target_ready` only when all blocking tracks are ready, `below_target` only when at least one confirmed blocking gap has confidence >= `.75`, otherwise `insufficient_evidence`. Publish an overall class estimate only when at least three of four anchors agree within one class.
- [ ] Persist learner-thinking elapsed, evaluator elapsed, stage started/updated timestamps, and outer elapsed separately. Model latency never consumes the learner's 240/300/180-second thinking budgets.
- [ ] Add `stage_started_at`, `last_learner_interaction_at`, `learner_elapsed_ms`, and `evaluator_elapsed_ms` to `school_sessions`; server transitions update them under the same row lock as placement state.
- [ ] Permit at most one automatic continuation per profile/release. A second incomplete run becomes `diagnostic_incomplete` with an honest next step.
- [ ] Make `insufficient_evidence` resumable while unused diagnostic work remains. `/school/state` must route to “Let’s finish finding your starting point” with one Resume action; a terminal insufficient session creates at most one linked continuation and never exposes a dead Continue button.

### Task 3.3: Browser-prove placement conclusions

- [ ] Through the real UI, record two independent clean traces each for Class 5->5, Class 5->4, Class 5->3, and Class 5->2.
- [ ] Record contradictory, insufficient, bilingual, abandoned/resumed, duplicate-submit, provider-unscorable, and no-key-leak traces.
- [ ] Verify every question is understandable, tied to its primary standard, and followed by supportive progress language without coaching the answer.

**Phase 3 gate:** every controlled conclusion is reproducible in browser and database evidence; the time cap fires; no static one-size-fits-all test remains.

## Phase 4: Readiness Path And Finite Support

### Task 4.1: Compile focused readiness paths from confirmed gaps

**Files:**
- Modify: `app/services/school/readiness_path.py`
- Modify: `app/api/school_rebuild_routes.py`
- Create: `tests/hardening/test_school_canonical_readiness_path.py`

- [ ] Build only the prerequisite closure of confirmed blocking gaps, ordered by lowest band then dependency order; never replay a full lower class.
- [ ] Snapshot non-blocking residual skills as watchlist and include the approved human-readable `deviation_note` when target access opens with watchlist items.
- [ ] Compile microdiagnostic -> teach -> guided -> independent -> transfer -> review units from authored content.
- [ ] Prove different evidence profiles create different valid plans and target-ready learners skip readiness work.

### Task 4.2: Implement path revisions and explicit termination

**Files:**
- Modify: `app/services/school/support.py`
- Modify: `app/services/school/journey.py`
- Modify: `src/services/schoolRebuild.ts`
- Modify: `src/app/school/support/[sessionId]/page.tsx`
- Modify: `src/components/school/support/SchoolSupportActivity.tsx`
- Create: `tests/hardening/test_school_canonical_readiness_support.py`

- [ ] Allow at most two support branches and two strategy revisions per standard during Readiness Path, with at most three immutable plan versions overall.
- [ ] A repeated failure changes reteach strategy and activity mode, not merely prompt wording.
- [ ] After caps, set `needs_external_support`, create an executable support plan, preserve completed evidence, and let the learner continue only where prerequisites permit.
- [ ] Qualifying readiness evidence updates the same projection and unlocks only standards whose prerequisite closure is ready.
- [ ] Retain `POST /school/support/start`, `GET /school/support/{session_id}`, and `POST /school/support/{session_id}/answer`; add/verify `POST /school/support/{session_id}/abandon`. Server-owned answer completion and abandon both produce explicit terminal outcomes. A support plan is a normal linked `school_sessions` flow with immutable plan lineage, not a display-only JSON block.
- [ ] Extend `src/services/schoolRebuild.ts` and `/school/support/[sessionId]` so creation, execution, reload, abandonment, and completion are usable in browser.

### Task 4.3: Harden target-class masterclass pause/resume/abandon

**Files:**
- Modify: `app/services/school_rebuild_curriculum.py` or canonical `app/services/school/teaching.py`
- Modify: `app/services/school_rebuild_masterclass.py` or canonical `app/services/school/support.py`
- Modify: `app/api/school_rebuild_routes.py`
- Create: `tests/integration/test_school_canonical_masterclass_lineage.py`

- [ ] Persist a real `linked_session_id` FK from paused curriculum to masterclass; never bury the only link in JSON.
- [ ] Preserve exact curriculum position during pause. Answer while paused returns `423 curriculum_paused_for_masterclass`.
- [ ] Resume only after server verifies the linked masterclass is complete.
- [ ] Abandon endpoint resolves the interrupt without readiness credit and still consumes the 1-2 cap.
- [ ] On the third same-skill trigger in one target chapter, do not branch again; record `masterclass_cap_exceeded`, create an executable support plan, and surface it in parent report.

### Task 4.4: Browser-prove readiness and support termination

- [ ] In the authenticated School profile, run two different below-target evidence sets and verify visibly different Readiness Paths.
- [ ] Trigger strategy revision, two linked support branches, abandon one branch, complete one, and force the terminal external-support path; reload at every transition.
- [ ] Verify the UI never deadlocks, never repeats a consumed activity, and returns to the exact parent plan node. Reconcile plan versions, reservations, linked sessions, cap counters, evidence, and projection rows after each branch.

**Phase 4 gate:** focused paths differ by evidence; repeated failure changes strategy and terminates; pause/resume preserves position; abandon cannot farm retries; recap unlocks exactly the correct target standards.

## Phase 5: Target Curriculum Adaptation, Memory, Reports, And Language

### Task 5.1: Compile target chapter overlays without omitting curriculum

**Files:**
- Modify: `app/services/school/journey.py`
- Modify: `app/services/school/teaching.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `src/services/schoolRebuild.ts`
- Create: `src/app/school/reviews/[sessionId]/page.tsx`
- Create: `tests/hardening/test_school_canonical_target_overlay.py`

- [ ] Start from the complete authored chapter plan, then overlay prerequisite reminders, watchlist probes, extra guided items, review schedule, modality fallback, and language scaffolds.
- [ ] Never skip required chapter outcomes because placement said ready or because a prerequisite is weak.
- [ ] Prove a target-ready learner and a recap learner receive observably different but curriculum-complete plans.
- [ ] Remove a resolved weakness from active hot context after qualifying evidence; retain history in longitudinal evidence.
- [ ] Add `GET /school/reviews/due`, `POST /school/reviews/start`, `GET /school/reviews/{session_id}`, `POST /school/reviews/{session_id}/answer`, and `POST /school/reviews/{session_id}/abandon`. Starting creates a normal linked School session from due projection rows; answering writes `review_check` evidence through the same transaction/projector; abandoning keeps the standard `review_due` and schedules the next honest action.
- [ ] Add a canonical `/school/reviews/[sessionId]` learner route using `SchoolTutorWorkspace`; reload, abandon, and completion follow normal session contracts and return to `/school` through backend state.

### Task 5.2: Build hot-session and longitudinal memory from committed evidence

**Files:**
- Create: `app/services/school/memory.py`
- Modify: `app/services/school_rebuild_state.py` or canonical `app/services/school/state.py`
- Create: `tests/hardening/test_school_canonical_memory.py`

- [ ] Hot memory contains current plan/activity, recent attempts, active misconception, hints/support used, language mode, and pending evaluation; it is refreshed from committed session/evidence after every transition.
- [ ] Longitudinal memory contains current banded projections, evidence recency, review due state, recurring blockers, support history, and growth trend.
- [ ] Session start reads the current projection version and scheduled reviews; stale summaries or generic career profiles never override School evidence.

### Task 5.3: Keep language confidence separate from certification

**Files:**
- Create: `app/services/school/language.py`
- Modify: `app/db/schema.sql`
- Modify: existing language-confidence migration/table only if schema changes are required
- Create: `tests/hardening/test_school_canonical_language_boundary.py`

- [ ] Support `en`, `hi`, and `hi_en` for explanation, orientation, glossary, and hints.
- [ ] Update `lang.en_production_confidence` with alpha `.20` only from real unscaffolded-English success, hint/glossary frequency, and certification-language mismatch.
- [ ] It controls scaffold availability and English-first invitations only. A fuzz test varies it across `[0,1]` while readiness fields remain constant and requires identical readiness/mastery classification.
- [ ] No maintenance job or elapsed calendar time raises confidence without evidence.

### Task 5.4: Build live learner and parent reports

**Files:**
- Create: `app/services/school/reports.py`
- Create: `app/db/migrations/2026-07-13-007-school-parent-share-tokens.sql`
- Modify: `app/db/schema.sql`
- Modify: `app/db/schema_guard.py`
- Modify: `scripts/apply_migrations.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `src/services/schoolRebuild.ts`
- Modify: `src/components/school/reports/LearnerGrowthSummary.tsx`
- Modify: `src/components/school/reports/ParentGrowthReport.tsx`
- Modify: `src/app/school/reports/page.tsx`
- Modify: `src/app/school/parent/page.tsx`
- Create: `tests/hardening/test_school_canonical_reports.py`

- [ ] Reports query current committed projections and evidence, not cached prose or completed-session counters.
- [ ] Add `GET /school/reports/learner` and `GET /school/reports/parent`; both return public-safe evidence references and the projection/release/plan versions used to build the report.
- [ ] Show strengths, active gaps, growth since placement, support used, review due, curriculum progress, capped support, and next action with evidence references and validity caveats.
- [ ] Keep the first viewport calm: summary and one next action; methodology and full history use progressive disclosure.
- [ ] Parent access uses authenticated ownership or scoped expiring share token; public report data excludes hidden rubrics/answers/private planner state.
- [ ] Add `school_parent_share_tokens` with hashed token, owner, report scope, expiry, revoked timestamp, created timestamp, and last-access timestamp. Add create/revoke endpoints for the owner and a scoped read endpoint; raw tokens are returned once, never stored, and cannot access sessions/evidence outside the report projection.

### Task 5.5: Add backend-truth-driven gamification without touching mastery

**Files:**
- Create: `app/services/school/gamification.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `src/services/schoolRebuild.ts`
- Modify: `src/app/school/page.tsx`
- Modify: `src/components/school/catalog/SchoolClassHome.tsx`
- Create: `tests/hardening/test_school_canonical_gamification.py`

- [ ] Derive streaks from committed certifying-evidence days only; guided/bridge retries cannot farm a streak.
- [ ] Derive badges deterministically from current evidence/projection/session facts and recompute them at request time. Persist only a first-earned timestamp if a later product requirement needs it.
- [ ] Expose one read-only `GET /school/gamification` payload so the frontend cannot independently invent streaks or badges.
- [ ] Keep streak/badge state out of `SchoolAttemptEvidence`, the readiness projector, placement, and unlock policies. A fuzz test requires identical classification with all gamification values varied.
- [ ] Present progress as restrained chapter-map feedback using the persisted coach palette; do not add a competing dashboard, decorative card wall, or raw score pressure for children.

### Task 5.6: Browser-compare adapted journeys and live reports

- [ ] Run one target-ready and one recap-completed learner through the same chapter; record the different valid plan nodes, scaffolds, watchlist probes, reviews, and support decisions.
- [ ] Resolve one weakness and verify it leaves active tutor context but remains in historical report evidence.
- [ ] Open learner and parent reports, create/revoke an expiring parent share, execute a due review, and verify every visible claim traces to current projection/evidence IDs.
- [ ] Repeat at mobile/tablet/desktop emulated viewports with normal and Fast 3G; capture console/network/accessibility results.

**Phase 5 gate:** target-ready/recap plans differ correctly; resolved gaps leave active context; reports reconcile to evidence; language preference changes scaffolding but never certification.

## Phase 6: Complete Class 2-5 English Content Release

### Task 6.1: Author in dependency-ordered batches

**Files:**
- Create/modify: `app/content/school/chapters/english/class_{2..5}/*.json`
- Create/modify: `app/content/school/prerequisites/english/*.json`
- Modify: `app/content/school/review_registry.json`
- Modify: `scripts/validate_school_content.py`
- Modify: `scripts/audit_school_content_semantics.py`

- [ ] Batch A: all prerequisite units and Class 2 modules.
- [ ] Batch B: Class 3 modules.
- [ ] Batch C: Class 4 modules.
- [ ] Batch D: Class 5 modules.
- [ ] Include units, picture reading, self-assessments, listening/speaking, and other release structural modules, not just 47 chapter titles.
- [ ] Meet the gold gate for every learner-servable module. Expected corpus size is greater than 4,500 substantive activities; count alone never overrides semantic audit.
- [ ] Run deterministic self-grading against every answer key and rubric fixture; require every assessment to grade its own approved answer correctly and reject known wrong answers.
- [ ] Record structural audit, answer-key self-check, rubric challenge examples, editorial/pedagogical review, copyright-similarity result, and one browser teaching run per module in the review registry. No draft or generated seed content enters production catalog.

### Task 6.2: Replace the serving loader and quarantine seeds

**Files:**
- Modify: `app/content/school/content_loader.py`
- Modify: `app/api/school_rebuild_routes.py`
- Modify: `app/services/school/placement.py`
- Modify: `app/services/school/teaching.py`
- Create: `tests/hardening/test_school_canonical_catalog_completeness.py`

- [ ] Serve the catalog only when release structural modules and all required approved content are present.
- [ ] Fail hard on malformed approved content; omit drafts intentionally; never silently skip a malformed approved module.
- [ ] Remove active imports of `school_v3_blueprints`, old `school_rebuild_chapters`, template-generated legacy JSON, and old placement bank.
- [ ] Assert the production loader serves the exact release catalog and no generated pattern corpus.

### Task 6.3: Browser-sample every release structure before class promotion

- [ ] For each Class 2-5 batch, browser-run first, middle, and final normal modules plus every special module type: picture reading, listening/speaking, self-assessment, game/offline action, and review.
- [ ] Complete at least one full chapter per class and verify locked-state enforcement, chapter -> level -> tutor navigation, persisted avatar/palette, activity rendering, evidence writes, report updates, and return-to-map behavior.
- [ ] Do not promote a class batch when any sampled module has unclear instructions, factual/rubric errors, broken media fallback, overflow, console errors, or answer-key leakage.

**Phase 6 gate:** complete release coverage; zero structural/semantic audit failures; every assessment validates; intended catalog is production-served; seed/template content is not an authority.

## Phase 7: Entitlements, Full Browser QA, And Legacy Retirement

### Task 7.1: Audit the approved free/paid boundary

**Files:**
- Modify: canonical School route/service entitlement checks
- Modify: frontend School state/actions
- Create: `tests/hardening/test_school_canonical_entitlements.py`

- [ ] Verify the Phase 2 enforcement remains: onboarding, placement, complete readiness report, and one demonstration lesson total are free; readiness path, ongoing curriculum, masterclasses, longitudinal reports, and scheduled reviews are paid/sponsored.
- [ ] Attempt bypass by clearing cookies/local state, replaying start requests, changing class/subject, and calling canonical start endpoints. Backend entitlement and one-demo ledger remain authoritative.

### Task 7.2: Re-audit child-data and authorization boundaries

**Files:**
- Create: `tests/hardening/test_school_canonical_child_data.py`
- Modify: analytics/report prompt builders as required

- [ ] Verify model prompts still contain only current approved content, compact learner context, and the current answer.
- [ ] Verify analytics still receives derived event types, not unrestricted child transcripts.
- [ ] Unauthorized users cannot read sessions, answers, evidence, projections, reports, linked sessions, or share tokens belonging to another user.
- [ ] Export/deletion and parent/guardian access paths are explicit before under-13 or school launch claims.

### Task 7.3: Run the supported browser/device matrix

**Files:**
- Create: `docs/qa/school-canonical-launch-qa.md`

- [ ] Authenticated School Chrome profile on `theopenassets@gmail.com`; preserve Ryuk data.
- [ ] Emulated `390x844`, `768x1024`, `1440x900` every phase; real Android phone/tablet and iOS/iPad hardware at gold slice, complete-content, and launch gates.
- [ ] Chrome/Edge current and previous; iOS/iPadOS Safari current and previous; macOS Safari current; Firefox best effort.
- [ ] Normal and Fast 3G; microphone granted, denied, interrupted, unavailable; keyboard-only; screen-reader names/status; WCAG 2.2 AA.
- [ ] Complete ready, below-target, weak/support, bilingual, mic denied, provider delayed, reload pending, abandon/resume, duplicate, unauthorized, no-key-leak, paywall/demo, due-review, and parent-report journeys.
- [ ] Require zero P0, no unexpected console error, overflow, overlap, inaccessible primary action, stale backend state, or visual regression from the approved aid.

### Task 7.4: Retire legacy only after measured cutover

**Files:**
- Create: `scripts/audit_school_legacy_retirement.py`
- Modify: legacy route redirects/imports after the release window
- Create: `tests/hardening/test_school_canonical_legacy_retirement.py`

- [ ] Require at least 90% of active School learners on canonical release/profile/plan lineage.
- [ ] Require zero P0 issues for 14 consecutive days.
- [ ] Keep legacy APIs read-only for one release window, then remove mounted imports and write paths.
- [ ] Archive old services/content with a migration manifest and reconciliation counts; do not delete historical evidence required by reports or disputes.
- [ ] Keep `/subjects`, `/subjects/v2`, and `/subjects/v3` as canonical `/school` redirects until external links are no longer observed.

**Phase 7 gate:** supported browser journeys pass; database evidence and reports reconcile; cost/latency budgets are observed; retirement criteria are met before legacy removal.

## Quantitative Completion Definition

The implementation is complete only when all of the following are true:

- The verified 2026-27 Class 2-5 English release, including structural modules, is production-served.
- All learner-servable modules pass the gold structural and semantic content gate.
- Placement can reproducibly conclude Class 5 readiness at Classes 5, 4, 3, or 2 from controlled evidence, with bounded insufficient states.
- Readiness paths are prerequisite-focused and finite; target support cannot deadlock or loop.
- Every flow updates one banded learner projection through one transactional projector.
- Readiness/mastery can regress and cannot be inflated by hints, scaffolds, language preference, streaks, badges, or legacy history.
- Parent/learner claims trace to evidence IDs and current projection version.
- Deterministic API p95 is under 2 seconds; evaluator-independent policy under 500 ms; pending ack under 1 second; local Qwen p95 is monitored against 90 seconds without a short failure timeout; hosted evaluation targets 8 seconds then pending.
- Model COGS remains under 15% of net School subscription revenue; 25% triggers provider/item/pricing review rather than silent pedagogy reduction.
- The full authenticated browser matrix passes with database assertions and the dedicated School QA account.
- Legacy runtime no longer has active write authority after the measured retirement gate.

## Review And Commit Discipline

For every task:

1. Write the focused failing test or browser reproduction.
2. Run it and capture the expected failure.
3. Implement only the task-owned behavior.
4. Run focused tests and `git diff --check`.
5. Run a subagent specification review, then a separate code-quality/product review.
6. Fix Critical/Important findings and rerun focused evidence.
7. Commit only task-owned files with a scoped message after checking the dirty worktree.
8. At phase gates, run authenticated browser QA and database assertions before beginning the next phase.
