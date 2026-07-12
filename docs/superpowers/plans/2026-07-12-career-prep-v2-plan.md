# Career Prep V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Career Prep evidence-safe, longitudinally personalized, tutor-grounded, and fully navigable through a 9+ browser experience across Interview Prep, GD Prep, Interview Test, and GD Test.

**Architecture:** Keep the existing LangGraph prep engine and structured assessment engine. Add stable task/evidence contracts and a closed Career skill taxonomy at the backend boundary, then project the resulting history through existing learning-graph, report, and runtime seams into a continuity-focused frontend.

**Tech Stack:** FastAPI, Pydantic, PostgreSQL/SQLAlchemy, LangGraph, Next.js 15, TypeScript, React, Tailwind, Chrome DevTools CDP.

---

### Task 1: Stop false Career completion and persist exact task context

**Files:**
- Create: `app/services/career_task_contract.py`
- Modify: `app/services/session_service.py:5060-5155`
- Modify: `app/services/rubric_engine.py:50-430`
- Modify: `app/graph/nodes/evaluate.py`
- Test: `tests/hardening/test_career_v2_contracts.py`

- [ ] Add a compact failing contract test proving `place_user("interview", self_report="fluent")` selects a start node but never calls `upsert_mastery` for preceding Career nodes.
- [ ] Add a failing test proving an `EvaluationPacket` contains `active_role` and the exact `task_contract.context_id`, `prompt_id`, `semantic_anchors`, `participant_claims`, and `evidence_policy` stored in session state.
- [ ] Implement the immutable contract:

```python
@dataclass(frozen=True)
class CareerTaskContract:
    prompt_id: str
    context_id: str
    active_role: str = ""
    active_topic: str = ""
    semantic_anchors: tuple[str, ...] = ()
    participant_claims: tuple[dict[str, str], ...] = ()
    evidence_policy: str = "learner_owned_or_sourced"
    hypothetical: bool = False
```

- [ ] Populate the contract whenever an independent, transfer, pressure, or bridge task is committed; keep it unchanged until that visible prompt is answered.
- [ ] For Career modules, make placement choose language difficulty only. Do not write completion, readiness, mastery, or pass counters.
- [ ] Run only the new Task 1 tests and verify the placement and packet failures turn green.

### Task 2: Fail closed on unsupported evidence, ambiguous participants, and fake transfer

**Files:**
- Modify: `app/services/rubric_engine.py`
- Modify: `app/services/rubrics.py`
- Modify: `app/content/data/group_discussion.json`
- Modify: `app/content/data/interview.json`
- Test: `tests/hardening/test_career_v2_contracts.py`

- [ ] Add four failing tests: unsourced `300%` external claim cannot satisfy GD evidence; GD08 fails without the assigned participant ID; GD10 fails when two clauses resolve to the same stance; Interview transfer fails when semantic anchors do not match the assigned context.
- [ ] Add evidence classification to the evaluation result:

```python
EvidenceType = Literal["learner_owned", "sourced_external", "analogy", "hypothetical", "unsupported"]

@dataclass(frozen=True)
class EvidenceAssessment:
    evidence_type: EvidenceType
    source_status: Literal["not_needed", "named", "missing"]
    epistemic_quality: float
```

- [ ] Never let deterministic reconciliation override evaluator errors tagged `unsupported_evidence`, `unverified`, or `source_missing`.
- [ ] Resolve GD08 identity only from `task_contract.participant_claims`; fail closed when none is assigned.
- [ ] Resolve GD10 distinctness from structured stance values attached to different participant IDs, not positive/negative trigger words in the learner answer.
- [ ] Validate Interview transfer against `task_contract.semantic_anchors` and `context_id`; remove `_INTERVIEW_TRANSFER_MARKER_GROUPS`.
- [ ] Align INT02 content, rubric, feedback, and bridge criteria around required strength, specific situation, learner action, and observable impact.
- [ ] Replace unattributed factual curriculum examples with labelled hypotheticals or non-numerical analogies.

### Task 3: Make readiness/mastery and test validity evidence-backed

**Files:**
- Modify: `app/services/rubric_engine.py:4100-4205`
- Modify: `app/services/simulation_service.py:2380-3335`
- Modify: `app/services/assessment_plan.py`
- Modify: `app/services/session_service.py:3450-3530, 5520-5575`
- Modify: `app/services/learning_profile.py:500-610`
- Test: `tests/hardening/test_career_v2_contracts.py`

- [ ] Add failing tests proving duplicate prompt/context evidence counts once, all score-excluded turns cannot produce `final`, and invalid/insufficient reports never enter prompt memory or durable strengths.
- [ ] Store distinct evidence IDs as `sha256(user_id, node_id, prompt_id, context_id, attempt_type)` and derive stage counts from unique IDs.
- [ ] Define report validity from scorable/excluded counts:

```python
if scorable == 0 and excluded > 0:
    validity = "invalid_simulation"
elif scorable < minimum or coverage < required:
    validity = "insufficient_evidence"
elif excluded / max(1, scorable + excluded) >= 0.25:
    validity = "partial"
else:
    validity = "final"
```

- [ ] Add `focus_plan` to `GDPlan`, built from canonical prior GD gaps, and place those IDs into the coverage ledger without forcing the model to repeat a specific sentence.
- [ ] Exclude invalid/insufficient reports from generic memory writes and future prompt summaries while preserving their report rows and integrity notes.
- [ ] Make `_update_session_learning_delta` idempotent with an `applied_evaluation_ids` set in persisted runtime state.

### Task 4: Build stable longitudinal skills, scoped memory, and session history

**Files:**
- Create: `app/services/career_skill_taxonomy.py`
- Modify: `app/services/learning_profile.py`
- Modify: `app/db/repo.py:1580-1745`
- Modify: `app/storage/pg_store.py`
- Modify: `app/api/me_routes.py`
- Modify: `app/ai/prompts.py:145-260, 500-600`
- Test: `tests/hardening/test_career_v2_contracts.py`

- [ ] Define stable learner-facing skill IDs for Interview and GD, with legacy aliases mapping hashed prose to canonical IDs.
- [ ] Add a failing test proving paraphrased gaps merge, authoritative progression mastery wins over profile readiness, and Interview prompt memory excludes GD-only gaps and invalid reports.
- [ ] Replace delete-and-reinsert report profiles with reconciliation: increment cumulative attempts, update trend evidence, and transition previously covered gaps to `resolved` only when the new report explicitly demonstrates that skill.
- [ ] Store transition provenance inside `evidence_json`:

```python
{"status": "improving", "previous_status": "active_gap", "report_id": "report:s1",
 "latest_score": 0.78, "trend": [0.61, 0.70, 0.78], "evidence_ids": ["..."]}
```

- [ ] Merge profile and progression rows by canonical ID; explicit `node_mastered` is authoritative.
- [ ] Add `scope_career_memory(memory, module_id, task_type)` and call it before prep prompts and assessment plans.
- [ ] Build `session_history` from report rows plus grouped prep events, returning timestamp, task type, module, session ID, status, score/readiness, evidence excerpt, and next action.
- [ ] Stop labelling vector-similarity order as recency; legacy memory is supplemental and task-scoped, while the learning graph is the canonical Career memory source.

### Task 5: Replace hardcoded coaching with grounded role/topic scenarios

**Files:**
- Create: `app/services/career_scenarios.py`
- Modify: `app/services/session_service.py:1080-2605`
- Modify: `app/services/content_personalization.py`
- Modify: `app/graph/nodes/bridge.py`
- Modify: `app/ai/prompts.py`
- Test: `tests/hardening/test_career_v2_contracts.py`

- [ ] Add failing tests for a nontechnical role, active GD transfer topic, a hypothetical departure, failed-criterion bridge selection, and mandatory open production after scaffolding.
- [ ] Replace Backend/Platform/engineering literals with structured scenario slots from role family, active role, safe profile facts, and neutral fallbacks.
- [ ] Mark invented practice premises `hypothetical=True` and render “Hypothetical practice” visibly; never present the premise as learner history.
- [ ] Pass `active_gd_prompt_topic` directly to `render_gd_bridge_exercise`; profile topics are used only when there is no active task.
- [ ] Select bridge exercises by missing criterion before band distance. Closed scaffolds must be followed by one spoken/open-production task before returning to evaluation.
- [ ] Anchor deterministic feedback only to evaluator evidence quotes and vary acknowledgement syntax; remove arbitrary truncated-answer prepending.
- [ ] Consume `allowed_praise` in the prompt contract and keep celebratory wording restricted to earned transfer/pressure/mastery evidence.

### Task 6: Expose accurate history, profile editing, billing, and targeted navigation

**Backend files:**
- Modify: `app/api/me_routes.py`
- Modify: `app/db/repo.py`
- Modify: `app/storage/pg_store.py`
- Modify: `app/billing/models.py`
- Modify: `app/api/billing_routes.py`

**Frontend files:**
- Modify: `src/services/me.ts`
- Modify: `src/services/billing.ts`
- Modify: `src/types/index.ts`
- Modify: `src/app/profile/page.tsx`
- Modify: `src/app/career/page.tsx`
- Modify: `src/app/(gamified)/map/page.tsx`
- Modify: `src/components/shared/PathMap.tsx`
- Modify: `src/components/billing/PaywallModal.tsx`
- Modify: `src/components/shared/SimulationReportModal.tsx`

- [ ] Add `created_at`, `session_history`, canonical skill label, and active-session target to the `/me/learning-graph` contract.
- [ ] Render Recent Sessions and Reports in Profile; test reports reopen through `/api/session/{id}/report`, prep rows show evidence and next action.
- [ ] Add `PATCH /me/career-profile` with the existing target-role, interview-goal, GD-topic, custom-topic, and resume-text validation contract. Persist it through `PgStore.update_career_profile()` and expose `updateCareerProfile()` in `src/services/me.ts`.
- [ ] Add a bounded Edit Career Profile panel using that endpoint; do not reopen onboarding.
- [ ] Route `Practice this gap` to `/map?focus=<canonical-node-id>` and scroll/highlight the exact node. Report primary actions use the same mapping; Return to Map remains secondary.
- [ ] Rename module-only `Resume` to `Continue path`; show `Resume session` only when the backend returns a real session ID.
- [ ] Display `Checkpoint passed`, `Needs practice`, and `Mastered` distinctly, with readiness and remaining evidence instead of repeating “Ready for next skill.”
- [ ] Render the wallet from `AppSessionProvider.balance` everywhere. Use quote `free`, `cost`, and `reason`; remove the unsupported “first couple of tries” sentence.
- [ ] Validate recommendation `href` as an internal path and navigate to it rather than always opening Profile.

### Task 7: Finish simulator and modal UX/accessibility

**Files:**
- Create: `src/components/shared/AccessibleDialog.tsx`
- Modify: `src/components/billing/PaywallModal.tsx`
- Modify: `src/components/billing/PacksModal.tsx`
- Modify: `src/components/simulator/EndSessionConfirmModal.tsx`
- Modify: `src/components/simulator/SimulatorShell.tsx`
- Modify: `src/components/shared/ScenarioPicker.tsx`
- Modify: `src/components/billing/CreditsBadge.tsx`
- Modify: `src/app/(professional)/simulator/interview/page.tsx`
- Modify: `src/app/(professional)/simulator/gd/page.tsx`

- [ ] Reuse one dialog primitive with role/label, initial focus, tab containment, Escape, backdrop handling, and focus restoration.
- [ ] Replace duplicate Save for Later/Leave with `Leave and save`; expose a distinct abandon action only when backend abandonment exists.
- [ ] Compact mobile simulator headers to logo/back plus End & Score; move balance/status into a secondary row.
- [ ] Rename GD Tension to Discussion Intensity and use neutral, focusable explanatory copy.
- [ ] Add `aria-pressed` to scenario choices, fieldset/legend semantics, selected-state names, and a compact “Using for this assessment” profile preview.
- [ ] Raise low-contrast microcopy to AA and include the visible balance in the credit button accessible name.
- [ ] Run TypeScript and Lighthouse after this batch; fix every newly introduced error and the known contrast failure.

### Task 8: Browser acceptance and completion audit

**Runtime:**
- Frontend: `http://localhost:3000` from `/private/tmp/zidd-career-prep-frontend`
- Backend: `http://127.0.0.1:8000` from `/private/tmp/zidd-career-prep-backend`
- Chrome: CDP `9222`, profile `Chrome-Zidd-CareerPrep`

- [ ] Verify current branches, clean startup, authenticated Ryuk profile, and a QA credit balance explicitly authorized by the user.
- [ ] Interview Prep: complete representative pitch, weakness/STAR, role-fit, and closing tasks; verify grounded feedback, bridge production, readiness, history, and next-session carry-over.
- [ ] GD Prep: complete evidence, build-on, quiet/dominator, and consensus tasks on two topics; verify active-topic continuity and participant contracts.
- [ ] Interview Test: complete a full round, use Clarify and Move On, end with confirmation, inspect score validity/breakdown, reopen report from Profile, and launch targeted practice.
- [ ] GD Test: complete a full round, request an active persona, verify discussion-style contributions, prior-gap coverage, end confirmation, final validity, and targeted practice.
- [ ] Reload mid-prep, mid-test, and after report. Verify real Resume Session links and no duplicate charges.
- [ ] Check Profile, map, tutor, simulator, and report at desktop and 390x844. Run Lighthouse snapshot and require Accessibility >= 98 with no contrast or accessible-name failures.
- [ ] Run focused backend Career V2 contracts, backend syntax compilation, frontend TypeScript, lint, and existing lightweight contract scripts. Do not run unrelated broad suites unless a touched shared contract requires it.
- [ ] Dispatch final spec and code-quality reviews, fix all Critical/Important findings, then perform a requirement-by-requirement completion audit before marking the goal complete.
