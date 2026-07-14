# School Prep Live Browser QA - Open Assets

Date: 2026-07-10

## Scope

Live browser QA was run against the actual school-prep Chrome profile:

- Chrome profile: `~/Library/Application Support/Google/Chrome-Zidd-SchoolPrep`
- CDP port: `9225`
- Frontend: `http://localhost:3001`
- Backend: `http://127.0.0.1:8088`
- Account verified in `/profile`: `[SCHOOL_QA_ACCOUNT]`
- User id: `google:116037578533700807149`
- Ryuk was not used or reset.

Open Assets school run data was reset before the clean run:

- `school_sessions`: 1 row deleted
- `learning_events`: 0 rows deleted
- `school_results`: 0 rows deleted
- `school_skill_mastery`: 0 rows deleted
- Active school profile was kept in place.

## Current Product Surface

Official rebuilt frontend surface currently has only:

- `/school`
- `/school/onboarding`
- `/school/placement`

There is no rebuilt learner-facing `/school` recap path, readiness report, target curriculum, tutor, or masterclass UI yet.

Legacy/V2/V3 service code exists elsewhere, but it is not the current canonical `/school` product surface tested here.

## What Placement Questions Are Based On

The live placement questions are not generated from NCERT chapter content.

They come from `app/content/school_rebuild_placement_bank.py`, a small authored Class 3 English diagnostic bank. The items check broad English foundations:

- Class 2 sentence detail
- Class 2 vocabulary in context
- Class 2 complete sentence
- naming words
- Class 3 main idea
- because/but connectors
- past tense
- reason answers

Personalization is currently very limited:

- Uses saved profile target class and subject.
- Only supports English Class 3.
- Uses prior difficulty signals only for ordering/prioritizing the first snapshot items.
- Does not generate a user-specific diagnostic module.
- Does not teach, scaffold, explain, or adapt during the run.

Evaluation is deterministic exact/accepted-answer matching. No LLM tutor or open-answer rubric is involved in this placement slice.

## Live Browser Run

Path:

1. `/profile` verified Open Assets identity.
2. `/school` showed `Class 3 · English`.
3. `/school` next action showed `Start readiness check`.
4. Clicked `START READINESS CHECK`.
5. `/school/placement` showed `Start your first snapshot`.
6. Clicked `START READINESS CHECK`.

Observed start bug:

- The start button became disabled and the page stayed on the start screen.
- Returning to `/school` showed `Continue readiness check`, proving the backend session had started.
- Reopening `/school/placement` resumed correctly and showed the first question.

Weak learner run:

| Step | Stage | Visible skill | Prompt | Answer used |
| --- | --- | --- | --- | --- |
| 0 | Snapshot 0/18 | Understand a simple sentence | Where did Rina sit? | wrong |
| 1 | Snapshot 1/18 | Use context to understand a word | In the sentence, what does tiny mean? | late |
| 2 | Snapshot 2/18 | Find the main idea | What is the passage mostly about? | A school race |
| 3 | Snapshot 3/18 | Answer with a reason | Why did Kabir switch on the lamp? | wrong |
| 4 | Snapshot 4/18 | Write a complete sentence | Complete the sentence: The bird is ___ on a branch. | wrong |
| 5 | Snapshot 5/18 | Recognize naming words | Which word names a thing in the sentence? | morning |
| 6 | Snapshot 6/18 | Use because to give a reason | Tara carried an umbrella ___ it was raining. | wrong |
| 7 | Snapshot 7/18 | Use past tense | Choose the past-tense word from the sentence. | the |
| 8 | Targeted 8/18 | Understand sentence detail | What did Nila put in the basket? | wrong |
| 9 | Targeted 9/18 | Use sentence clues for meaning | What does clever mean here? | round |
| 10 | Targeted 10/18 | Complete a sentence | The dog ___ after the ball. | wrong |
| 11 | Targeted 11/18 | Identify naming words | Which word names a person? | board |
| 12 | Targeted 12/18 | Find the main idea | What is the passage mostly about? | children buying shoes |
| 13 | Targeted 13/18 | Use but for contrast | Ravi wanted to play outside, ___ it was too hot. | wrong |
| 14 | Targeted 14/18 | Use past tense | Which word shows the past action? | I |
| 15 | Targeted 15/18 | Give a reason from clues | Why did Sana drink water? | wrong |

After step 15, the placement page showed:

- `TARGETED CHECK · 16/18`
- `Readiness check saved`
- `This phase has saved your placement evidence. The readiness report and recap path come next.`

Then `/school` showed:

- `Continue readiness check`
- `The readiness check is still in progress. Target class is not unlocked yet.`

## Persisted Backend State

After the live browser run, persisted state for Open Assets was:

```text
school_sessions:
  session_id: 2b37432a-eabb-4bf2-8c50-2c4479ebc4a3
  api_version: rebuild
  flow_type: placement
  subject_id: english
  class_no: 3
  status: active
  current_stage: targeted_diagnostic
  engine_stage: targeted_diagnostic
  answered: 16

learning_events:
  snapshot: 8 attempts, score_sum 0.0
  targeted_diagnostic: 8 attempts, score_sum 0.0
```

## Findings

1. Critical: weak placement path dead-ends.

The placement page says the evidence is saved, but the backend keeps the session `active` and `/school` routes the learner back to placement. There is no readiness report, recap path, or curriculum handoff.

2. Critical: placement page has a start-screen race.

After clicking start, the page can remain stuck on the disabled start screen while the backend session exists. Reloading/resuming fixes it, but a real child would think the product froze.

3. Important: there is no teaching loop.

The learner gets one question after another. There is no feedback, explanation, supportive correction, hint, native-language support, bridge item, or tutor response.

4. Important: the diagnostic is not actually personalized enough.

It is a fixed Class 3 English bank with slight ordering from profile signals. It is not a staged module generated from onboarding plus prior answers in a deep way.

5. Important: content is not NCERT-chapter aligned.

Questions are valid as isolated English foundations, but they are not tied to current NCERT chapter structure or target-class curriculum readiness.

6. Important: UI/UX is still not a child learning experience.

The current UI is a plain form flow. It does not explain progress, reduce anxiety, celebrate effort, show why questions are asked, or make the next step clear after weak performance.

7. Important: no post-placement product exists on the canonical surface.

The frontend has labels for recap/curriculum actions, but no actual rebuilt routes or screens for them.

## Current Verdict

The product cannot currently complete school prep end to end.

It can onboard a Class 3 English learner and collect placement attempts. It cannot yet place the learner into a real readiness report, build a recap path, teach recap content, run masterclasses, unlock target curriculum, or teach the target class.

This confirms the current school tutor is still a placement prototype, not a school-prep product.

## Post-QA Fix Verification

After the dead-end was reproduced, the placement terminal-state bug was fixed and verified against the same live Open Assets browser session.

Verified browser state:

- `/school` now shows `View readiness report`.
- `/school` says `Open Assets Learner, your readiness check evidence is saved.`
- `/school` explicitly blocks on `Readiness report and recap path are not built yet.`
- `/school/placement` now resolves to the saved placement screen instead of loading forever.

Verified persisted state:

```text
session_id: 2b37432a-eabb-4bf2-8c50-2c4479ebc4a3
status: complete
current_stage: targeted_diagnostic
answered: 16
completed_at: 2026-07-10 15:49:13.582786+00:00
```

Remaining product truth is unchanged: report, recap, masterclass, and target-class curriculum are still not built on the canonical `/school` surface.

## Phase 3 Addendum - Readiness Report + Recap Shell

After the terminal placement fix, the next slice added:

- `/school/placement/report`
- `/school/recap`
- `school_placement_reports` persisted report table
- recap sessions stored in the generic `school_sessions` table with `flow_type=recap`
- state routing from completed placement -> report -> active recap

Migration verification:

```text
school_placement_reports columns:
  active_learning_class_no
  allowed_next_actions_json
  blocking_skills_json
  created_at
  evaluated_class_no
  evidence_summary_json
  learner_summary
  parent_summary
  placement_session_id
  placement_status
  profile_version_id
  recommended_recap_modules_json
  report_id
  subject_id
  target_class_no
  unlock_state
  updated_at
  user_id
  watchlist_skills_json

indexes:
  idx_school_placement_reports_user_updated
  school_placement_reports_pkey
  school_placement_reports_user_id_placement_session_id_key
```

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q

50 passed, 16 warnings

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA was rerun in the same Chrome profile on CDP port `9225`.

Verified report screen:

```text
URL: http://localhost:3001/school/placement/report

Your starting point
Class 2 foundations first
We will first build your Class 2 foundations, then move you toward Class 3 English.
Across 16 placement checks, Zidd found 8 foundation areas to rebuild before regular chapter teaching.
0/16 checks strong
Start recap path
```

Verified foundation areas:

```text
Recognize naming words
Understand a simple sentence
Use context to understand a word
Write a complete sentence
Answer with a reason
Find the main idea
Use because to give a reason
Use past tense
```

Live QA found and fixed one report bug:

- Initial report showed duplicate foundation areas for multi-skill placement items.
- Root cause: report grouped by raw skill id while two skill ids could share one learner-facing label.
- Fix: merge public blocking skills by `(label, source_class_no)` and refresh deterministic reports on read.
- Re-verified in browser: report now shows 8 foundation areas instead of 10 duplicated rows.

Verified recap screen:

```text
URL: http://localhost:3001/school/recap

Rebuild foundations first
8 focused modules before target-class chapters
Each module teaches the weak area, gives guided support, then asks for an independent check.
```

Verified `/school` after recap start:

```text
NEXT STEP
Continue recap
Open Assets Learner, continue your recap path from where you left off.
The learner is rebuilding prerequisite foundations before class chapters.
```

Phase 3 verdict:

- Completed placement no longer dead-ends.
- The readiness report is evidence-backed from committed placement learning events.
- The recap path is created from the stored report, not from client-provided skills.
- The recap surface is still a path shell, not a full teaching loop yet.
- Masterclass, recap module execution, target-class chapter teaching, and NCERT-depth content remain unbuilt.

## Phase 4 Addendum - Executable Recap Module

The next slice made the recap path executable for the success path:

- `GET /school/recap` now returns `progress`, `current_activity`, and `last_feedback`.
- `POST /school/recap/{session_id}/answer` grades the current activity server-side.
- Correct guided answer advances to an independent check.
- Correct independent answer marks the module complete and advances to the next module.
- Stale activity submissions return `409 unexpected_recap_activity`.
- Recap answers write `learning_events` with `task_type=school_rebuild_recap`.
- Public responses still hide answer keys, accepted answers, rubrics, thresholds, and model answers.

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q

53 passed, 16 warnings

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA was rerun in Chrome profile `Chrome-Zidd-SchoolPrep` on CDP `9225`.

Initial recap activity:

```text
URL: http://localhost:3001/school/recap

0/8 modules complete
GUIDED CHECK / CLASS 2
Recap: Recognize naming words
The teacher reads a book.
Which word names a person?
teacher
reads
book
the
```

Clicked `teacher`.

After guided answer:

```text
Good. Now try the same skill without hints.
INDEPENDENT CHECK / CLASS 2
Recap: Recognize naming words
The red flower opened in the morning.
Which word names a thing?
flower
opened
red
morning
```

Clicked `flower`.

After independent answer:

```text
1/8 modules complete
Good. This module is complete, so the next foundation area is ready.
GUIDED CHECK / CLASS 2
Recap: Understand a simple sentence
Rina sat on the mat. The mat was near the window.
Where did Rina sit?
```

Returning to `/school` still showed:

```text
NEXT STEP
Continue recap
Open Assets Learner, continue your recap path from where you left off.
The learner is rebuilding prerequisite foundations before class chapters.
```

Backend log check:

```text
POST /school/recap/6858c84b-0385-4f4c-8331-9ffa3b4887af/answer 200
POST /school/recap/6858c84b-0385-4f4c-8331-9ffa3b4887af/answer 200
GET /school/state 200
```

Phase 4 verdict:

- The first recap module can now be taught, checked, completed, and advanced in the live browser.
- This is still not the complete recap product: incorrect-answer bridge behavior has a backend state path but has not been live-browser QA'd yet.
- Masterclass detours, repeated-failure caps, full recap completion -> curriculum unlock, target-class teaching, and NCERT-depth content remain unbuilt.

## Phase 5 Addendum - Recap Bridge + Masterclass Detour

The next slice made recap support reactive on wrong answers:

- A wrong guided answer keeps the same module active and opens a bridge activity.
- A wrong bridge answer opens a focused masterclass activity for the same skill.
- A wrong masterclass answer stays in focused masterclass support instead of bouncing the learner back to bridge.
- A correct masterclass answer returns to the independent check.
- A correct independent check after the detour completes the module and advances the recap path.
- Known recap modules without bespoke masterclass content reuse the bridge prompt and accepted answer set, instead of requiring the learner to type the skill name.
- Public responses still hide answer keys, accepted answers, rubrics, thresholds, and model answers.

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q

56 passed, 16 warnings

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA was rerun in Chrome profile `Chrome-Zidd-SchoolPrep` on CDP `9225`.

Starting live state:

```text
URL: http://localhost:3001/school/recap

1/8 modules complete
GUIDED CHECK / CLASS 2
Recap: Understand a simple sentence
Rina sat on the mat. The mat was near the window.
Where did Rina sit?
```

Submitted wrong guided answer: `window`.

After wrong guided answer:

```text
Not yet. Zidd will slow this down with a bridge check before moving ahead.
BRIDGE SUPPORT / CLASS 2
Recap: Understand a simple sentence
Slow down and rebuild the clue for understand a simple sentence before trying again.
Read the sentence again and look for the thing after the action.
Nila put three mangoes in the basket. What thing did she put there?
```

Submitted wrong bridge answer: `river`.

After wrong bridge answer:

```text
Not yet. Zidd is opening a focused masterclass for this skill.
FOCUSED MASTERCLASS / CLASS 2
Masterclass: Understand a simple sentence
Masterclass: rebuild understand a simple sentence in more depth before the independent check.
Masterclass: slow down and rebuild Understand a simple sentence before trying independently.
Nila put three mangoes in the basket. What thing did she put there?
```

Submitted correct masterclass answer: `mangoes`.

After correct masterclass answer:

```text
Good. Now try the same skill without hints.
INDEPENDENT CHECK / CLASS 2
Recap: Understand a simple sentence
Now try understand a simple sentence without hints.
Nila put three mangoes in the basket.
What did Nila put in the basket?
```

Submitted correct independent answer: `mangoes`.

After independent answer:

```text
2/8 modules complete
Good. This module is complete, so the next foundation area is ready.
GUIDED CHECK / CLASS 2
Recap: Use context to understand a word
The tiny seed was so small that Meera held it on one finger.
What does tiny mean?
small
heavy
angry
late
```

Repeated-masterclass edge QA was also rerun after the reviewer pass:

```text
2/8 modules complete
GUIDED CHECK / CLASS 2
Recap: Use context to understand a word
The tiny seed was so small that Meera held it on one finger.
What does tiny mean?
small
heavy
angry
late
```

Submitted wrong guided answer: `heavy`.

```text
BRIDGE SUPPORT / CLASS 2
Use the clue after the word. The tiny seed was so small.
Which clue tells you the meaning of tiny?
small
heavy
late
angry
```

Submitted wrong bridge answer: `heavy`.

```text
FOCUSED MASTERCLASS / CLASS 2
Masterclass: Use context to understand a word
Masterclass: rebuild use context to understand a word in more depth before the independent check.
Which clue tells you the meaning of tiny?
small
heavy
late
angry
```

Submitted wrong masterclass answer: `heavy`.

```text
Not yet. Stay in the masterclass and try one more supported check.
FOCUSED MASTERCLASS / CLASS 2
Masterclass: Use context to understand a word
Which clue tells you the meaning of tiny?
small
heavy
late
angry
```

Submitted correct masterclass answer: `small`.

```text
Good. Now try the same skill without hints.
INDEPENDENT CHECK / CLASS 2
Recap: Use context to understand a word
The clever crow dropped stones into the pot and raised the water.
What does clever mean here?
smart
sleepy
wet
round
```

Phase 5 verdict:

- The recap module support loop now works in the live browser for guided miss -> bridge miss -> masterclass support/retry -> independent check -> module advance.
- The UI labels the focused masterclass state explicitly instead of hiding it under guided/bridge copy.
- This is still not the full school prep product: repeated-failure cap, full recap completion -> curriculum unlock, target-class curriculum teaching, learner weakness profile updates, and NCERT-depth content remain unbuilt.

## Phase 6 Addendum - Recap Revision Levels After Repeated Masterclass Misses

The next slice made repeated masterclass failure change the learning graph instead of looping forever:

- First wrong masterclass answer keeps the learner in focused masterclass support.
- Second wrong masterclass answer expands the same module into three revision levels.
- Correct Revision Level 1 advances to Revision Level 2.
- Correct Revision Level 2 advances to Revision Level 3.
- Correct Revision Level 3 returns to the independent check.
- Every revision level is a typed attempt in the learning-event ledger.
- Public responses still hide answer keys, accepted answers, rubrics, thresholds, and model answers.

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q

58 passed, 16 warnings

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA was rerun in Chrome profile `Chrome-Zidd-SchoolPrep` on CDP `9225`.

Starting live state after completing module 3:

```text
3/8 modules complete
GUIDED CHECK / CLASS 2
Recap: Write a complete sentence
A bird is sitting on a branch.
Complete the sentence: The bird is ___ on a branch.
```

Submitted wrong guided answer: `flying`.

```text
Not yet. Zidd will slow this down with a bridge check before moving ahead.
BRIDGE SUPPORT / CLASS 2
Recap: Write a complete sentence
Slow down and rebuild the clue for write a complete sentence before trying again.
A complete sentence needs the action word. The dog ran.
What action word completes the sentence: The dog ___ after the ball?
```

Submitted wrong bridge answer: `jumped`.

```text
Not yet. Zidd is opening a focused masterclass for this skill.
FOCUSED MASTERCLASS / CLASS 2
Masterclass: Write a complete sentence
Masterclass: rebuild write a complete sentence in more depth before the independent check.
What action word completes the sentence: The dog ___ after the ball?
```

Submitted first wrong masterclass answer: `jumped`.

```text
Not yet. Stay in the masterclass and try one more supported check.
FOCUSED MASTERCLASS / CLASS 2
Masterclass: Write a complete sentence
What action word completes the sentence: The dog ___ after the ball?
```

Submitted second wrong masterclass answer: `jumped`.

```text
This needs a short revision run before trying again.
REVISION LEVEL 1 / CLASS 2
Revision 1: Write a complete sentence
Revision level 1: rebuild write a complete sentence with a fresh supported check before returning to the main path.
Revision 1: start with the strongest clue. A complete sentence needs the action word. The dog ran.
What action word completes the sentence: The dog ___ after the ball?
```

Submitted correct Revision Level 1 answer: `ran`.

```text
Good. Move to the next revision level.
REVISION LEVEL 2 / CLASS 2
Revision 2: Write a complete sentence
Revision 2: try a nearby example. The dog ran after the ball.
Complete the sentence: The dog ___ after the ball.
```

Submitted correct Revision Level 2 answer: `ran`.

```text
Good. Move to the next revision level.
REVISION LEVEL 3 / CLASS 2
Revision 3: Write a complete sentence
Revision 3: one final supported check. Masterclass: slow down and rebuild Write a complete sentence before trying independently.
What action word completes the sentence: The dog ___ after the ball?
```

Submitted correct Revision Level 3 answer: `ran`.

```text
Good. Now try the same skill without hints.
INDEPENDENT CHECK / CLASS 2
Recap: Write a complete sentence
Now try write a complete sentence without hints.
The dog ran after the ball.
Complete the sentence: The dog ___ after the ball.
```

Phase 6 verdict:

- Repeated failure inside masterclass now creates a visible, typed revision run in the same recap module.
- The frontend labels revision levels clearly and the module cards show that revision levels exist when needed.
- This is still not the full school prep product: completing all recap modules and unlocking target-class curriculum is the next required slice, followed by target-class teaching, growth-profile updates, and NCERT-depth content.

## Phase 7 Addendum — Recap Completion Unlocks Target Class

Scope:

- Complete the recap path and use that evidence to unlock the learner's target-class curriculum landing.
- Keep `/school/state`, `/school/recap`, and `/school/curriculum` consistent after recap completion.
- Do not leak answer keys, accepted answers, rubrics, thresholds, or model answers in public responses.

Automated checks after the final fix:

```text
pytest tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q

63 passed, 16 warnings

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Supabase/runtime setup:

```text
.venv/bin/python scripts/apply_migrations.py
Applied 16 migration file(s) and validated runtime schema.

GET http://127.0.0.1:8088/health
{"status":"ok","service":"zidd-engine","ollama_reachable":true,"storage_writable":true,"active_sessions":0}
```

Live browser QA used the required Chrome profile and CDP port:

```text
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9225 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-Zidd-SchoolPrep" \
  http://localhost:3001/auth/login
```

Authenticated test identity visible in the browser:

```text
Open Assets
[SCHOOL_QA_ACCOUNT]
```

The learner had already completed the remaining recap modules in the same browser profile:

```text
Module 4 independent: ran
Module 5 guided/independent: dark, thirsty
Module 6 guided/independent: Aman caring for plants, children reading in a library
Module 7 guided/independent: because, because
Module 8 guided/independent: went, played
```

Initial live regression found:

```text
/school
NEXT STEP
Start target class
Open Assets Learner, your recap path is complete. Start your target class: Class 3 English.

/school/recap
RECAP NOT OPEN
Start from your saved readiness report
No active recap path is open yet.
```

Root cause:

- `/school/state` and `/school/curriculum` used the latest recap session, including completed recap sessions.
- `GET /school/recap` only looked for an active recap session.
- Once recap status became `complete`, the route returned `404 recap_session_not_found`, so the completed page could not show the "Open target class" button.

Fix:

- `GET /school/recap` now returns the latest recap path, active or completed.
- `POST /school/recap/start` now returns an existing latest recap path instead of creating a duplicate after completion.
- Added regression coverage: `test_get_school_recap_returns_completed_path_after_unlock` and `test_start_school_recap_after_completion_is_idempotent`.

Live browser verification after restart:

```text
/school/recap
CLASS 2 FOUNDATION PATH
8/8 modules complete
Recap path complete.
Your target class is unlocked from this evidence.
OPEN TARGET CLASS

All 8 modules show COMPLETE.
```

Clicking `OPEN TARGET CLASS`:

```text
/school/curriculum
TARGET CLASS
Class work unlocked
CLASS 3 · ENGLISH
Santoor
Target class is unlocked. Full chapter teaching is the next build slice.

CHAPTER MAP
CHAPTER 1 Santoor Chapter 1
...
CHAPTER 12 Santoor Chapter 12
Teaching loop opens in the next build step.
```

Phase 7 verdict:

- Recap completion now unlocks the target-class curriculum landing from backend state, not client-only fallback.
- The completed recap page and school dashboard now agree.
- The curriculum page is intentionally only a landing/chapter preview in this slice.
- Remaining product gap is large: chapter titles/content are still placeholder-quality and target-class teaching is not implemented yet.

## Phase 8 Addendum — First Target-Class Chapter Teaching Loop

Scope:

- Replace the Class 3 curriculum placeholder for Chapter 1 with a real, backend-owned teaching session.
- Use official NCERT only as the structural source. The official current Class 3 English book is `Santoor`; the first chapter is `Colours` in Unit 1 `Fun with Friends`.
- Store and serve original Zidd-authored teaching passages, checks, bridge support, and masterclass support.
- Carry recap weakness signals into the target-class session without letting the frontend invent state.

Official source checked:

```text
https://ncert.nic.in/textbook/pdf/cesa101.pdf
Santoor, Class 3, Unit 1 Fun with Friends, Chapter 1 Colours.
```

Automated checks after Phase 8:

```text
pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
       tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q

67 passed, 16 warnings

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors

.venv/bin/python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940
```

Backend behavior added:

- `POST /school/curriculum/start`
- `GET /school/curriculum/{session_id}`
- `POST /school/curriculum/{session_id}/answer`
- Active curriculum sessions now make `/school/state` return `next_action=resume_curriculum`.
- Public curriculum responses hide answer keys, accepted answers, model answers, rubrics, and thresholds.
- Learning events are written for each curriculum attempt with `task_type=school_rebuild_curriculum`.

Auth/runtime:

```text
GET http://127.0.0.1:8088/health
{"status":"ok","service":"zidd-engine","ollama_reachable":true,"storage_writable":true,"active_sessions":0}
```

Live browser QA used Chrome profile `Chrome-Zidd-SchoolPrep` on CDP `9225`, authenticated as:

```text
Open Assets
[SCHOOL_QA_ACCOUNT]
```

Landing before start:

```text
/school/curriculum
TARGET CLASS
Class work unlocked
CLASS 3 · ENGLISH
Santoor
Target class is unlocked. Start Chapter 1 when you are ready.
START CHAPTER 1

CHAPTER 1
Colours
Ready

CHAPTER 2..12
Locked
```

After starting Chapter 1:

```text
Colours
Santoor · Fun with Friends
0/5 levels complete

GUIDED CHECK / ANSWER WITH A REASON
Learn: Why sharing colours helps
Mira has red and blue crayons. Dev has green and yellow crayons.
What should Mira and Dev do so both pictures can have more colours?

Options:
share / hide / break / throw
```

Wrong guided answer: `hide`.

```text
Not yet. Zidd will slow this chapter level down with a bridge check.
BRIDGE SUPPORT / ANSWER WITH A REASON
Which action helps both children use more colours?
share / sleep / argue / forget
```

Wrong bridge answer: `sleep`.

```text
Not yet. Zidd is opening a focused masterclass for this chapter skill.
FOCUSED MASTERCLASS / ANSWER WITH A REASON
Masterclass: use a colour clue and a why clue.
What action helps Asha and Kabir both finish their pictures?
share / hide / tear / wait
```

Correct masterclass answer: `share`.

```text
Good. Now try the same chapter skill without hints.
INDEPENDENT CHECK / ANSWER WITH A REASON
Ravi has brown and black. Tara has pink and grey.
What should Ravi and Tara do so both posters can have the needed colours?
```

Correct independent answer: `share`.

```text
1/5 levels complete
Good. This chapter level is complete, so the next level is ready.
GUIDED CHECK / USE CONTEXT TO UNDERSTAND A WORD
Learn: Use colour words from context
Which colour word describes the sky?
blue / green / fresh / rain
```

Dashboard resume check:

```text
/school
NEXT STEP
Continue class
Open Assets Learner, continue Class 3 English: Colours.
The learner is now working inside the target-class teaching loop.
CONTINUE CLASS
```

Resume page check:

```text
/school/curriculum
Colours
1/5 levels complete
Level 1 COMPLETE
Level 2 IN PROGRESS
```

Additional local review finding and fix:

- Found a curriculum scoring bug in `_answer_matches`: accepted answers were matched as substrings.
- Example risk: accepted answer `b` could incorrectly mark `banana` as correct.
- Added regression coverage: `test_curriculum_short_answer_requires_exact_match_not_substring`.
- Fixed scoring to normalize punctuation and require exact phrase or word-boundary match.

Full chapter completion browser QA after the scoring fix:

```text
Chrome profile:
--remote-debugging-port=9225
--user-data-dir=/Users/18abhinav07/Library/Application Support/Google/Chrome-Zidd-SchoolPrep

/school/curriculum
2/5 levels complete
GUIDED CHECK / IDENTIFY ACTION WORDS
Which word is an action?
jump / rainbow / wall / children

Clicked: jump
Typed independent answer: writes

/school/curriculum
3/5 levels complete
GUIDED CHECK / ALPHABETICAL ORDER
Which word comes first in alphabet order?
blue / green / red

Clicked wrong answer: green
BRIDGE SUPPORT / ALPHABETICAL ORDER
Which first letter comes earliest: b, g, or r?

Clicked wrong answer: g
FOCUSED MASTERCLASS / ALPHABETICAL ORDER
Which word comes first?
brown / orange / yellow

Clicked correct answer: brown
INDEPENDENT CHECK / ALPHABETICAL ORDER
Words: purple, black, white.
Which word comes first in alphabet order?

Typed independent answer: black

/school/curriculum
4/5 levels complete
GUIDED CHECK / WORD FRIENDS
Which new word do rain and bow make?
rainbow / rainball / bowrain / bowpaper

Clicked correct answer: rainbow
INDEPENDENT CHECK / WORD FRIENDS
rain + bow
Write the new word.

Typed independent answer: rainbow

/school/curriculum
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. The next chapter will open in a later slice.
Level 1 COMPLETE
Level 2 COMPLETE
Level 3 COMPLETE
Level 4 COMPLETE
Level 5 COMPLETE
```

Phase 8 verdict:

- The first target-class chapter now has a real backend-owned teaching loop.
- The loop uses the same proven support pattern as recap: guided check, bridge, focused masterclass, independent check, and level advancement.
- Recap weaknesses carry into the target-class session as context chips and backend session state.
- This is still only one authored chapter slice. The remaining Class 3 chapters and the full class 2-5 corpus still need real chapter-level content, not generated placeholders.

## Phase 9 Addendum — Chapter Sequencing and Chapter 2 Start

Scope:

- Remove the completed-chapter dead end.
- Add Chapter 2 `Badal and Moti` as a real original Zidd-authored teaching module.
- Preserve completed chapter history in backend state so the next start opens the next incomplete chapter.
- Update frontend completed-chapter UI from "later slice" to `Start next chapter`.

Official source checked:

```text
https://ncert.nic.in/textbook/pdf/cesa102.pdf
Santoor, Class 3, Chapter 2 Badal and Moti.
```

Implementation notes:

- Chapter 2 is not loaded from the seed blueprint because the seed files are still template-like and not pedagogically acceptable.
- The curriculum service now keeps `completed_chapter_ids`.
- `GET /school/curriculum` marks completed chapters as `complete` and the next teachable chapter as `ready`.
- `POST /school/curriculum/start` starts the next incomplete authored chapter.
- Public responses still strip `answer_key`, `accepted_answers`, `model_answer`, `rubric`, and `threshold`.

Automated checks after Phase 9:

```text
pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
       tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q

68 passed, 16 warnings

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors

.venv/bin/python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940
```

Runtime note:

```text
The first live browser attempt still opened Chapter 1 because the backend on port 8088
had been started without --reload and was serving the previous code. Restarting the
same 8088 backend from the current worktree fixed the mismatch.
```

Live browser QA used Chrome profile `Chrome-Zidd-SchoolPrep` on CDP `9225`.

Browser transcript after backend restart:

```text
/school/curriculum
Colours
0/5 levels complete
GUIDED CHECK / ANSWER WITH A REASON
What should Mira and Dev do so both pictures can have more colours?
share / hide / break / throw

Answered the remaining Chapter 1 path with correct independent checks.

/school/curriculum
Colours
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. Continue when you are ready for the next chapter.
START NEXT CHAPTER

Clicked START NEXT CHAPTER.

/school/curriculum
Badal and Moti
Santoor · Fun with Friends
0/5 levels complete
GUIDED CHECK / ANSWER WITH A REASON
Learn: Why caring changes the story
Badal sees a small puppy near the road on a cold evening.
What kind action does Badal want to take?
care for the puppy / leave the puppy / hide the puppy / run away
```

DB verification after live browser QA:

```text
latest curriculum session:
status=active
chapter_id=eng_c3_ch02
chapter_title=Badal and Moti
completed_chapter_ids=['eng_c3_ch01']

previous curriculum session:
status=complete
chapter_id=eng_c3_ch01
chapter_title=Colours
completed_chapter_ids=['eng_c3_ch01']
```

Phase 9 verdict:

- Chapter 1 no longer dead-ends.
- The learner can continue from a completed chapter into Chapter 2 from the same `/school/curriculum` surface.
- Chapter 2 has a real first teaching loop and five authored levels, but it has not yet been fully completed in browser QA.
- Remaining gap: continue scaling this chapter-by-chapter, and replace seed/template source-map titles for Chapters 3-12 with verified official titles and authored content.

## Phase 9 Follow-up — Chapter 2 Completion and Final Authored-Slice State

Scope:

- Complete Chapter 2 end to end in the dedicated School Prep browser profile.
- Verify support behavior still works inside Chapter 2.
- Fix the final authored-slice state so the UI does not show a dead "start next chapter" action after the last authored chapter.

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Chapter 2 live browser transcript:

```text
/school/curriculum
Badal and Moti
0/5 levels complete

Level 1:
guided answer: care for the puppy
independent answer: care for Moti

Level 2:
guided answer: Badal cares for Moti
independent answer: Badal and Moti become friends

Level 3:
guided wrong answer: Moti
result: Bridge support
bridge wrong answer: Moti
result: Focused masterclass
masterclass answer: helped
independent answer: played

Level 4:
guided answer: Can Moti stay with us?
independent answer: question

Level 5:
guided answer: kindness and friendship can help us
independent answer: friendship

Final chapter state:
Badal and Moti
5/5 levels complete
Chapter complete.
START NEXT CHAPTER
```

Defect found:

```text
After Chapter 2 completed, the session page and landing page still exposed a start-next action even though only Chapters 1-2 are authored right now.
This was a real UX/state defect: the backend start endpoint could reject the action, but the learner should not see a dead CTA.
```

Fix implemented:

- `public_curriculum_response()` now exposes `next_available_chapter` when a completed session has another authored chapter, otherwise `null`.
- Completed-session UI shows `Start Chapter N` only when `next_available_chapter` exists.
- Curriculum landing UI shows `All available chapters complete` instead of a start button when there is no ready authored chapter.
- Backend contract test covers completing Chapter 1, starting Chapter 2, completing Chapter 2, and receiving `409 all_curriculum_chapters_complete` on another start attempt.

Verified final live browser state after restart from current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE
BACK TO PATH

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Santoor Chapter 3 Locked
...
Chapter 12 Santoor Chapter 12 Locked

No START CHAPTER button is present.
```

Automated checks after the follow-up fix:

```text
.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
6 passed, 16 warnings

.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
       tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q
69 passed, 16 warnings

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors

.venv/bin/python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940
```

Follow-up verdict:

- Chapter 2 is now completed end to end in the live browser.
- The Chapter 2 support ladder works: wrong guided answer -> bridge; wrong bridge answer -> focused masterclass; correct masterclass answer -> independent check.
- The final authored-slice state no longer offers a dead next-chapter action.
- Remaining product gap is still content scale and pedagogy depth across all current NCERT English class 2-5 chapters, not this Chapter 1-2 sequencing loop.

## Phase 10 Addendum — Chapter 3 Best Friends

Scope:

- Replace the placeholder Class 3 Chapter 3 title with the official current NCERT chapter title.
- Add a real original Zidd-authored teaching loop for Chapter 3.
- Preserve the same backend-owned sequence: guided check -> bridge -> focused masterclass -> independent check -> level completion.
- Verify Chapter 3 starts after Chapter 2 and that the final authored-slice state moves from Chapter 2 to Chapter 3.

Official source checked:

```text
https://ncert.nic.in/textbook/pdf/cesa103.pdf
Santoor, Class 3, Chapter 3 Best Friends.
```

Implementation notes:

- `app/content/ncert_source_map/english/class_3.json` now names Chapter 3 as `Best Friends`.
- `app/services/school_rebuild_curriculum.py` now includes `CLASS_3_BEST_FRIENDS_CHAPTER`.
- Chapter 3 has five authored levels:
  - why friends work better together;
  - shape clue comprehension;
  - `a` / `an`;
  - writing about a friend;
  - action words.
- The authored content is NCERT-aligned structurally but does not copy the textbook body.

TDD evidence:

```text
Initial focused contract after writing the Chapter 3 tests:
2 failed, 5 passed

Expected failures:
- completed_second["next_available_chapter"] was None.
- third curriculum start returned no chapter because Chapter 3 was not authored yet.
```

Automated checks after implementation:

```text
.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
7 passed, 16 warnings

.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
       tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q
70 passed, 16 warnings

.venv/bin/python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 3 when you are ready.
START CHAPTER 3

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Ready
Chapter 4 Santoor Chapter 4 Locked
...
```

Clicked `START CHAPTER 3`.

```text
/school/curriculum
Best Friends
Santoor · Fun with Friends
0/5 levels complete
GUIDED CHECK / FIND THE MAIN IDEA
Learn: Why friends work better together

What should the shape friends do to make one complete picture?
together / fight / hide / erase
```

Completed Chapter 3 in browser:

```text
Level 1:
guided answer: together
independent answer: work together

Level 2:
guided answer: circle
independent answer: triangle

Level 3:
guided answer: an
independent answer: a

Level 4 support path:
guided wrong answer: round
result: Bridge support
bridge wrong answer: square
result: Focused masterclass
masterclass answer: My friend is helpful.
independent answer: My friend is kind.

Level 5:
guided answer: bark
independent answer: jump

Final state:
Best Friends
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Phase 10 verdict:

- Chapter 3 now starts correctly after Chapter 2.
- Chapter 3 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The final authored-slice state is now correct after Chapter 3, not Chapter 2.
- Remaining product gap: Chapters 4-12 still show placeholder titles and are locked until they have verified official titles plus authored teaching loops.

## Phase 11 Addendum — Chapter 4 Out in the Garden

Scope:

- Replace the placeholder Class 3 Chapter 4 title with the official current NCERT chapter title.
- Add a real original Zidd-authored teaching loop for Chapter 4.
- Preserve the backend-owned curriculum sequence and support ladder.
- Verify Chapter 4 starts after Chapter 3 and becomes the current final authored-slice state.

Official source checked:

```text
https://ncert.nic.in/textbook/pdf/cesa104.pdf
Santoor, Class 3, Unit 2 Toys and Games, Chapter 4 Out in the Garden.
```

Implementation notes:

- `app/content/ncert_source_map/english/class_3.json` now names Chapter 4 as `Out in the Garden`.
- `app/services/school_rebuild_curriculum.py` now includes `CLASS_3_OUT_IN_THE_GARDEN_CHAPTER`.
- Chapter 4 has five authored levels:
  - picture reading from a play scene;
  - ball action words;
  - kite action sequence;
  - joining play words with `and`;
  - safe outdoor play reason answers.
- The authored content is NCERT-aligned structurally but does not copy the textbook body.

TDD evidence:

```text
Initial focused contract after writing the Chapter 4 tests:
2 failed, 6 passed

Expected failures:
- completed_third["next_available_chapter"] was None.
- fourth curriculum start returned no chapter because Chapter 4 was not authored yet.
```

Automated checks after implementation:

```text
.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
8 passed, 16 warnings

.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
       tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q
71 passed, 16 warnings

.venv/bin/python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 4 when you are ready.
START CHAPTER 4

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Ready
Chapter 5 Santoor Chapter 5 Locked
...
```

Clicked `START CHAPTER 4`.

```text
/school/curriculum
Out in the Garden
Santoor · Toys and Games
0/5 levels complete
GUIDED CHECK / PICTURE READING
Learn: Read a play picture

What are the children mainly doing in the picture?
playing / sleeping / cooking / reading quietly
```

Completed Chapter 4 in browser:

```text
Level 1:
guided answer: playing
independent answer: open space

Level 2:
guided answer: bounce
independent answer: catch

Level 3 support path:
guided wrong answer: sleep
result: Bridge support
bridge wrong answer: eat
result: Focused masterclass
masterclass answer: pull
independent answer: pull

Level 4:
guided answer: sing and dance
independent answer: run and catch

Level 5:
guided answer: be careful
independent answer: play safely

Final state:
Out in the Garden
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Phase 11 verdict:

- Chapter 4 now starts correctly after Chapter 3.
- Chapter 4 completed end to end in the live browser.
- The support ladder was verified live on Level 3.
- The final authored-slice state is now correct after Chapter 4.
- Remaining product gap: Chapters 5-12 still show placeholder titles and are locked until they have verified official titles plus authored teaching loops.

## Phase 12 Addendum — Chapter 5 Talking Toys

Scope:

- Replace the placeholder Class 3 Chapter 5 title with the official current NCERT chapter title.
- Add a real original Zidd-authored teaching loop for Chapter 5.
- Preserve the backend-owned curriculum sequence and support ladder.
- Verify Chapter 5 starts after Chapter 4 and becomes the current final authored-slice state.

Official source checked:

```text
https://ncert.nic.in/textbook/pdf/cesa105.pdf
Santoor, Class 3, Unit 2 Toys and Games, Chapter 5 Talking Toys.
```

Implementation notes:

- `app/content/ncert_source_map/english/class_3.json` now names Chapter 5 as `Talking Toys`.
- `app/services/school_rebuild_curriculum.py` now includes `CLASS_3_TALKING_TOYS_CHAPTER`.
- Chapter 5 has five authored levels:
  - toy-shop story sequence;
  - toy vocabulary from context;
  - describing words;
  - plural words with `s` and `es`;
  - process order words for making activities.
- The authored content is NCERT-aligned structurally but does not copy the textbook body.

TDD evidence:

```text
Initial focused contract after writing the Chapter 5 tests:
2 failed, 7 passed

Expected failures:
- completed_fourth["next_available_chapter"] was None.
- fifth curriculum start returned no chapter because Chapter 5 was not authored yet.
```

Automated checks after implementation:

```text
.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
9 passed, 16 warnings

.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
       tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q
72 passed, 16 warnings

.venv/bin/python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 5 when you are ready.
START CHAPTER 5

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Ready
Chapter 6 Santoor Chapter 6 Locked
...
```

Clicked `START CHAPTER 5`.

```text
/school/curriculum
Talking Toys
Santoor · Toys and Games
0/5 levels complete
GUIDED CHECK / SEQUENCE STORY EVENTS
Learn: Follow the toy-shop story

Where does this story scene begin?
toy shop / bus stop / garden / library
```

Completed Chapter 5 in browser:

```text
Level 1:
guided answer: toy shop
independent answer: train

Level 2:
guided answer: doll
independent answer: marbles

Level 3:
guided answer: red
independent answer: soft elephant

Level 4 support path:
guided wrong answer: toy
result: Bridge support
bridge wrong answer: box
result: Focused masterclass
masterclass answer: brushes
independent answer: boxes

Level 5:
guided answer: first
independent answer: finally

Final state:
Talking Toys
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Hydration check:

```text
Reloaded /school/curriculum
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Santoor Chapter 6 Locked
...
```

Live UX issue observed:

- The deterministic curriculum turn often leaves selected option buttons disabled for several seconds before the next activity appears.
- One Level 3 guided transition took roughly 11 seconds before the independent check hydrated.
- This is not a correctness blocker for Chapter 5, but it is a real product-quality issue for children and should be handled with clearer pending states and latency profiling.

Phase 12 verdict:

- Chapter 5 now starts correctly after Chapter 4.
- Chapter 5 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The completion state persists after reloading the curriculum route.
- Remaining product gap: Chapters 6-12 still show placeholder titles and are locked until they have verified official titles plus authored teaching loops.

## Phase 13 Addendum — Chapter 6 Paper Boats

Scope:

- Replace the placeholder Class 3 Chapter 6 title with the official current NCERT chapter title.
- Add a real original Zidd-authored teaching loop for Chapter 6.
- Preserve the backend-owned curriculum sequence and support ladder.
- Verify Chapter 6 starts after Chapter 5 and becomes the current final authored-slice state.

Official source checked:

```text
https://ncert.nic.in/textbook/pdf/cesa106.pdf
Santoor, Class 3, Unit 2 Toys and Games, Chapter 6 Paper Boats.
```

Implementation notes:

- `app/content/ncert_source_map/english/class_3.json` now names Chapter 6 as `Paper Boats`.
- `app/services/school_rebuild_curriculum.py` now includes `CLASS_3_PAPER_BOATS_CHAPTER`.
- Chapter 6 has five authored levels:
  - identifying the story setting;
  - explaining a character feeling with a reason;
  - sequencing a helpful action;
  - using `he` and `she`;
  - using position words.
- The authored content is NCERT-aligned structurally but does not copy the textbook body.

TDD evidence:

```text
Initial focused contract after writing the Chapter 6 tests:
2 failed, 8 passed

Expected failures:
- completed_fifth["next_available_chapter"] was None.
- sixth curriculum start returned no chapter because Chapter 6 was not authored yet.
```

Automated checks after implementation:

```text
.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
10 passed, 16 warnings

.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
       tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q
73 passed, 16 warnings

.venv/bin/python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 6 when you are ready.
START CHAPTER 6

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Ready
Chapter 7 Santoor Chapter 7 Locked
...
```

Clicked `START CHAPTER 6`.

```text
/school/curriculum
Paper Boats
Santoor · Toys and Games
0/5 levels complete
GUIDED CHECK / IDENTIFY STORY SETTING
Learn: Find the story setting

Where does Meera put the paper boat?
stream / roof / cupboard / blackboard
```

Completed Chapter 6 in browser:

```text
Level 1:
guided answer: stream
independent answer: paper boats

Level 2:
guided answer: angry
independent answer: because he overturned her boats

Level 3:
guided answer: fold
independent answer: showed him how to make a boat

Level 4 support path:
guided wrong answer: he
result: Bridge support
bridge wrong answer: he
result: Focused masterclass
masterclass answer: he
independent answer: he

Level 5:
guided answer: under
independent answer: on

Final state:
Paper Boats
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Hydration check:

```text
Reloaded /school/curriculum
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 Santoor Chapter 7 Locked
...
```

Live UX issue observed:

- The route can stay on `LOADING CLASS` for more than 12 seconds after reload before the completed map appears.
- The start request also held `START CHAPTER 6` disabled for several seconds before hydrating into the chapter session.
- Correctness passed, but the pending/loading state remains too opaque for a child-facing product.

Phase 13 verdict:

- Chapter 6 now starts correctly after Chapter 5.
- Chapter 6 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The completion state persists after reloading the curriculum route.
- Remaining product gap: Chapters 7-12 still show placeholder titles and are locked until they have verified official titles plus authored teaching loops.

## Phase 14 Addendum — Chapter 7 The Big Laddoo

Scope:

- Replace the placeholder Class 3 Chapter 7 title with the official current NCERT chapter title.
- Add a real original Zidd-authored teaching loop for Chapter 7.
- Preserve the backend-owned curriculum sequence and support ladder.
- Verify Chapter 7 starts after Chapter 6 and becomes the current final authored-slice state.

Official source checked:

```text
https://ncert.nic.in/textbook/pdf/cesa107.pdf
Santoor, Class 3, Unit 3 Good Food, Chapter 7 The Big Laddoo.
```

Implementation notes:

- `app/content/ncert_source_map/english/class_3.json` now names Chapter 7 as `The Big Laddoo`.
- `app/services/school_rebuild_curriculum.py` now includes `CLASS_3_BIG_LADDOO_CHAPTER`.
- Chapter 7 has five authored levels:
  - understanding poem imagination;
  - classifying round things as food/not food;
  - using sense clues;
  - reading `pl`, `cl`, and `bl` blend words;
  - using float/sink vocabulary.
- The authored content is NCERT-aligned structurally but does not copy the textbook body.

TDD evidence:

```text
Initial focused contract after writing the Chapter 7 tests:
2 failed, 9 passed

Expected failures:
- completed_sixth["next_available_chapter"] was None.
- seventh curriculum start returned no chapter because Chapter 7 was not authored yet.
```

Automated checks after implementation:

```text
.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
11 passed, 16 warnings

.venv/bin/pytest tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
       tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
       tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
       tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
       tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
       tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
       tests/hardening/test_schema_security_contract.py \
       tests/hardening/test_school_rebuild_phase_0_1_contract.py \
       tests/hardening/test_onboarding_profile_contract.py -q
74 passed, 16 warnings

.venv/bin/python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

npm run test:school-rebuild-surface
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 7 when you are ready.
START CHAPTER 7

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Ready
Chapter 8 Santoor Chapter 8 Locked
...
```

Clicked `START CHAPTER 7`.

```text
/school/curriculum
The Big Laddoo
Santoor · Good Food
0/5 levels complete
GUIDED CHECK / UNDERSTAND POEM IMAGINATION
Learn: Imagine the big picture

What giant sweet is the poem asking us to imagine?
big laddoo / small seed / paper boat / green kite
```

Completed Chapter 7 in browser:

```text
Level 1:
guided answer: big laddoo
independent answer: big splash

Level 2:
guided answer: laddoo
independent answer: ball

Level 3:
guided answer: touch
independent answer: round and sweet

Level 4 support path:
guided wrong answer: cloud
result: Bridge support
bridge wrong answer: plum
result: Focused masterclass
masterclass answer: plum
independent answer: plum

Level 5:
guided answer: float
independent answer: sink

Final state:
The Big Laddoo
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Hydration check:

```text
Reloaded /school/curriculum
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Santoor Chapter 8 Locked
...
```

Live UX issue observed:

- The curriculum route again stayed on `LOADING CLASS` for more than 16 seconds before the completed map appeared.
- Correctness passed, but this loading behavior remains a product-quality issue for children and should be profiled rather than accepted as normal.

Phase 14 verdict:

- Chapter 7 now starts correctly after Chapter 6.
- Chapter 7 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The completion state persists after reloading the curriculum route.
- Remaining product gap: Chapters 8-12 still show placeholder titles and are locked until they have verified official titles plus authored teaching loops.

## Phase 15 Addendum - Chapter 8 `Thank God!`

Source used:

- Official NCERT structural source: `https://ncert.nic.in/textbook/pdf/cesa108.pdf`
- Scope used from source: chapter title, broad story shape, fruit/weight reasoning, opposite words, `is`/`are`, and fruit-salad sequencing.
- Stored curriculum remains Zidd-authored original teaching content and checks; no textbook body text was copied.

Implementation notes:

- Added Chapter 8 as `eng_c3_ch08`, title `Thank God!`, book `Santoor`, unit `Good Food`.
- Added five teachable levels:
  - Choose the lighter gift
  - Understand the joke
  - Use opposite words
  - Choose is or are
  - Order salad steps
- Added guided, bridge/masterclass, and independent evidence paths for each level.
- Updated the Class 3 source map title from placeholder `Santoor Chapter 8` to `Thank God!`.

TDD evidence:

```text
Initial focused contract before implementation:
2 failed, 10 passed

Post-implementation focused contract:
12 passed, 16 warnings
```

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_8_*.py \
  tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py \
  tests/hardening/test_school_rebuild_phase_9_*.py \
  tests/hardening/test_school_rebuild_phase_10_*.py \
  tests/hardening/test_school_rebuild_phase_11_*.py \
  tests/hardening/test_school_rebuild_phase_12_*.py \
  tests/hardening/test_school_rebuild_phase_13_*.py \
  tests/hardening/test_school_rebuild_phase_14_*.py
75 passed, 16 warnings

python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

node scripts/check-school-rebuild-frontend.mjs
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 8 when you are ready.
START CHAPTER 8

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Ready
Chapter 9 Santoor Chapter 9 Locked
...
```

Clicked `START CHAPTER 8`.

```text
/school/curriculum
Thank God!
Santoor - Good Food
0/5 levels complete
GUIDED CHECK / INFER A PRACTICAL REASON
Learn: Notice weight clues

The farmer had to walk a long way. Which fruit was easiest to carry?
grapes / watermelons / pumpkins / coconuts
```

Completed Chapter 8 in browser:

```text
Level 1:
guided answer: grapes
independent answer: grapes were light

Level 2:
guided answer: watermelons
independent answer: watermelons would hurt more

Level 3:
guided answer: light
independent answer: short

Level 4 support path:
guided wrong answer: is
result: Bridge support
bridge wrong answer: is
result: Focused masterclass
masterclass answer: is
independent answer: is

Level 5:
guided answer: first
independent answer: finally

Final state:
Thank God!
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Hydration check:

```text
Reloaded /school/curriculum
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
Chapter 11 Santoor Chapter 11 Locked
Chapter 12 Santoor Chapter 12 Locked
```

Live UX issue observed:

- The curriculum route still needs a long hydration wait before the completed map appears.
- Correctness passed, but the slow loading behavior remains a product-quality issue for children and should be profiled separately.

Phase 15 verdict:

- Chapter 8 now starts correctly after Chapter 7.
- Chapter 8 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The completion state persists after reloading the curriculum route.
- Remaining product gap: Chapters 9-12 still show placeholder titles and are locked until they have verified official titles plus authored teaching loops.

## Phase 16 Addendum - Chapter 9 `Madhu's Wish`

Source used:

- Official NCERT structural source: `https://ncert.nic.in/textbook/pdf/cesa109.pdf`
- Scope used from source: chapter title, broad story shape, sharing/kindness, wish consequence, water-need lesson, food groups, `and`/`but`, and `because` reason answers.
- Stored curriculum remains Zidd-authored original teaching content and checks; no textbook body text was copied.

Implementation notes:

- Added Chapter 9 as `eng_c3_ch09`, title `Madhu's Wish`, book `Santoor`, unit `Good Food`.
- Added five teachable levels:
  - Notice kindness
  - Find the real need
  - Sort food words
  - Join ideas
  - Give a reason
- Added guided, bridge/masterclass, and independent evidence paths for each level.
- Updated the Class 3 source map title from placeholder `Santoor Chapter 9` to `Madhu's Wish`.

TDD evidence:

```text
Initial focused contract before implementation:
2 failed, 11 passed

Post-implementation focused contract:
13 passed, 16 warnings
```

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py \
  tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
  tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
  tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
  tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
  tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
  tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
41 passed, 16 warnings

python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

node scripts/check-school-rebuild-surface.mjs
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 9 when you are ready.
START CHAPTER 9

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Madhu's Wish Ready
Chapter 10 Santoor Chapter 10 Locked
...
```

Clicked `START CHAPTER 9`.

```text
/school/curriculum
Madhu's Wish
Santoor - Good Food
0/5 levels complete
GUIDED CHECK / INFER A CHARACTER QUALITY
Learn: Notice kindness

In this story pattern, Madhu shared his lunch with a hungry old man.

Who does Madhu share his food with?
old man / shopkeeper / teacher / farmer
```

Completed Chapter 9 in browser:

```text
Level 1:
guided answer: old man
independent answer: he was kind

Level 2:
guided answer: water
independent answer: water is important

Level 3:
guided answer: fruits
independent answer: samosa

Level 4 support path:
guided wrong answer: but
result: Bridge support
bridge wrong answer: but
result: Focused masterclass
masterclass answer: but
independent answer: but

Level 5:
guided answer: because
independent answer: because he needed water

Final state:
Madhu's Wish
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Hydration check:

```text
Reloaded /school/curriculum
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Madhu's Wish Complete
Chapter 10 Santoor Chapter 10 Locked
Chapter 11 Santoor Chapter 11 Locked
Chapter 12 Santoor Chapter 12 Locked
```

Live UX issues observed:

- The first guided answer returned `200 OK` on the backend but took roughly 10 seconds before the frontend advanced to the independent check.
- The curriculum route still needs a long hydration wait before the completed map appears.
- Correctness passed, but the response/render delay remains a product-quality issue for children and should be profiled separately.

Phase 16 verdict:

- Chapter 9 now starts correctly after Chapter 8.
- Chapter 9 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The completion state persists after reloading the curriculum route.
- Remaining product gap: Chapters 10-12 still show placeholder titles and are locked until they have verified official titles plus authored teaching loops.

## Phase 17 Addendum - Chapter 10 `Night`

Source used:

- Official NCERT structural source: `https://ncert.nic.in/textbook/pdf/cesa110.pdf`
- Scope used from source: chapter title, unit placement, broad night/day poem shape, sky vocabulary, sun movement picture, blend sounds, and sun compound words.
- Stored curriculum remains Zidd-authored original teaching content and checks; no textbook body text was copied.

Implementation notes:

- Added Chapter 10 as `eng_c3_ch10`, title `Night`, book `Santoor`, unit `The Sky`.
- Added five teachable levels:
  - Feel the night scene
  - Track the sun
  - Name sky things
  - Hear sky blends
  - Build sun words
- Added guided, bridge/masterclass, and independent evidence paths for each level.
- Updated the Class 3 source map title from placeholder `Santoor Chapter 10` to `Night`.

TDD evidence:

```text
Initial focused contract before implementation:
2 failed, 12 passed

Post-implementation focused contract:
14 passed, 16 warnings
```

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py \
  tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
  tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
  tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
  tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
  tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
  tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
42 passed, 16 warnings

python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

node scripts/check-school-rebuild-surface.mjs
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 10 when you are ready.
START CHAPTER 10

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Madhu's Wish Complete
Chapter 10 Night Ready
Chapter 11 Santoor Chapter 11 Locked
...
```

Clicked `START CHAPTER 10`.

```text
/school/curriculum
Night
Santoor - The Sky
0/5 levels complete
GUIDED CHECK / UNDERSTAND POEM MOOD
Learn: Feel the night scene

A poem can show time by using light and sound clues.

Which time of day is this scene about?
night / noon / morning / festival
```

Completed Chapter 10 in browser:

```text
Level 1:
guided answer: night
independent answer: dark and still

Level 2:
guided answer: hill
independent answer: behind the hill

Level 3:
guided answer: stars
independent answer: moon

Level 4 support path:
guided wrong answer: spoon
result: Bridge support
bridge wrong answer: storm
result: Focused masterclass
masterclass answer: sky
independent answer: sky

Level 5:
guided answer: sunlight
independent answer: sunset

Final state:
Night
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Hydration check:

```text
Reloaded /school/curriculum
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Madhu's Wish Complete
Chapter 10 Night Complete
Chapter 11 Santoor Chapter 11 Locked
Chapter 12 Santoor Chapter 12 Locked
```

Live UX issue observed:

- The curriculum route still needs a long hydration wait before the completed map appears.
- Correctness passed, but the response/render delay remains a product-quality issue for children and should be profiled separately.

Phase 17 verdict:

- Chapter 10 now starts correctly after Chapter 9.
- Chapter 10 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The completion state persists after reloading the curriculum route.
- Remaining product gap: Chapters 11-12 still show placeholder titles and are locked until they have verified official titles plus authored teaching loops.

## Phase 18 Addendum - Chapter 11 `Chanda Mama Counts the Stars`

Source used:

- Official NCERT structural source: `https://ncert.nic.in/textbook/pdf/cesa111.pdf`
- Scope used from source: chapter title, unit placement, Chanda Mama/moon framing, star-counting problem, Sun's help, `here`/`there`, and countable versus too-many-to-count groups.
- Stored curriculum remains Zidd-authored original teaching content and checks; no textbook body text was copied.

Implementation notes:

- Added Chapter 11 as `eng_c3_ch11`, title `Chanda Mama Counts the Stars`, book `Santoor`, unit `The Sky`.
- Added five teachable levels:
  - Notice the moon
  - Count the stars
  - Understand the Sun's help
  - Choose here or there
  - Can we count it?
- Added guided, bridge/masterclass, and independent evidence paths for each level.
- Updated the Class 3 source map title from placeholder `Santoor Chapter 11` to `Chanda Mama Counts the Stars`.

TDD evidence:

```text
Initial focused contract before implementation:
2 failed, 13 passed

Post-implementation focused contract:
15 passed, 16 warnings
```

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py \
  tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
  tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
  tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
  tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
  tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
  tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
43 passed, 16 warnings

python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

node scripts/check-school-rebuild-surface.mjs
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 11 when you are ready.
START CHAPTER 11

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Madhu's Wish Complete
Chapter 10 Night Complete
Chapter 11 Chanda Mama Counts the Stars Ready
Chapter 12 Santoor Chapter 12 Locked
```

Clicked `START CHAPTER 11`.

```text
/school/curriculum
Chanda Mama Counts the Stars
Santoor - The Sky
0/5 levels complete
GUIDED CHECK / UNDERSTAND CHANGING SHAPE
Learn: Notice the moon

Chanda Mama is a loving name for the moon.

Which sky body changes its visible shape?
moon / chair / pencil / drum
```

Completed Chapter 11 in browser:

```text
Level 1:
guided answer: moon
independent answer: the moon changes shape

Level 2:
guided answer: stars
independent answer: too many stars

Level 3:
guided answer: sun
independent answer: children and stars

Level 4 support path:
guided wrong answer: there
result: Bridge support
bridge wrong answer: there
result: Focused masterclass
masterclass answer: there
independent answer: there

Level 5:
guided answer: fingers
independent answer: hairs

Final state:
Chanda Mama Counts the Stars
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Hydration check:

```text
Reloaded /school/curriculum
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Madhu's Wish Complete
Chapter 10 Night Complete
Chapter 11 Chanda Mama Counts the Stars Complete
Chapter 12 Santoor Chapter 12 Locked
```

Live UX issues observed:

- The long inline CDP script hit a timing race at the final independent input; a direct DOM inspection showed the app had advanced correctly to the input state, and submitting from the visible state completed the chapter.
- The curriculum route still needs a long hydration wait before the completed map appears.
- Correctness passed, but the response/render delay remains a product-quality issue for children and should be profiled separately.

Phase 18 verdict:

- Chapter 11 now starts correctly after Chapter 10.
- Chapter 11 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The completion state persists after reloading the curriculum route.
- Remaining product gap: Chapter 12 still shows a placeholder title and is locked until it has a verified official title plus authored teaching loop.

## Phase 19 Addendum - Chapter 12 `Chandrayaan`

Source used:

- Official NCERT structural source: `https://ncert.nic.in/textbook/pdf/cesa112.pdf`
- Scope used from source: chapter title, unit placement, Rani's curiosity, moon-landing news, scientist/rocket explanation, `Chandra`/`Yaan` word parts, and Chandrayaan landing date.
- Stored curriculum remains Zidd-authored original teaching content and checks; no textbook body text was copied.

Implementation notes:

- Added Chapter 12 as `eng_c3_ch12`, title `Chandrayaan`, book `Santoor`, unit `The Sky`.
- Added five teachable levels:
  - Notice curiosity
  - Understand the news
  - Ask a scientist
  - Break the word
  - Write the date fact
- Added guided, bridge/masterclass, and independent evidence paths for each level.
- Updated the Class 3 source map title from placeholder `Santoor Chapter 12` to `Chandrayaan`.

TDD evidence:

```text
Initial focused contract before implementation:
2 failed, 14 passed

Post-implementation focused contract:
16 passed, 16 warnings
```

Automated checks:

```text
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py \
  tests/hardening/test_school_rebuild_phase_2_placement_contract.py \
  tests/hardening/test_school_rebuild_phase_3_report_recap_contract.py \
  tests/hardening/test_school_rebuild_phase_4_recap_execution_contract.py \
  tests/hardening/test_school_rebuild_phase_5_recap_support_contract.py \
  tests/hardening/test_school_rebuild_phase_7_recap_unlock_contract.py \
  tests/hardening/test_school_rebuild_phase_8_curriculum_teaching_contract.py -q
44 passed, 16 warnings

python scripts/validate_school_v3_content.py
school_v3_content_ok chapters=47 items=5405 chapter_checks=940

node scripts/check-school-rebuild-surface.mjs
School rebuild frontend surface check passed

npx tsc --noEmit
passed

npm run lint
No ESLint warnings or errors
```

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Browser transcript after restarting backend from the current worktree:

```text
/school/curriculum
Class work unlocked
Santoor
Target class is unlocked. Start Chapter 12 when you are ready.
START CHAPTER 12

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Madhu's Wish Complete
Chapter 10 Night Complete
Chapter 11 Chanda Mama Counts the Stars Complete
Chapter 12 Chandrayaan Ready
```

Clicked `START CHAPTER 12`.

```text
/school/curriculum
Chandrayaan
Santoor - The Sky
0/5 levels complete
GUIDED CHECK / INFER CHARACTER TRAIT
Learn: Notice curiosity

A curious person wants to know more. Rani keeps asking questions about the sky and the moon.

Which word describes Rani?
curious / sleepy / angry / careless
```

Completed Chapter 12 in browser:

```text
Level 1:
guided answer: curious
independent answer: she asked many questions

Level 2:
guided answer: moon
independent answer: india reached the moon

Level 3:
guided answer: scientist
independent answer: a rocket

Level 4 support path:
guided wrong answer: sun flower
result: Bridge support
bridge wrong answer: water
result: Focused masterclass
masterclass answer: chandra means moon
independent answer: chandra means moon

Level 5:
guided answer: 23 August 2023
independent answer: Chandrayaan landed on 23 August 2023.

Final state:
Chandrayaan
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE
No START CHAPTER button is present.
```

Hydration check:

```text
Reloaded /school/curriculum
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Colours Complete
Chapter 2 Badal and Moti Complete
Chapter 3 Best Friends Complete
Chapter 4 Out in the Garden Complete
Chapter 5 Talking Toys Complete
Chapter 6 Paper Boats Complete
Chapter 7 The Big Laddoo Complete
Chapter 8 Thank God! Complete
Chapter 9 Madhu's Wish Complete
Chapter 10 Night Complete
Chapter 11 Chanda Mama Counts the Stars Complete
Chapter 12 Chandrayaan Complete
```

Live UX issue observed:

- The curriculum route still needs a long hydration wait before the completed map appears.
- Correctness passed, but the response/render delay remains a product-quality issue for children and should be profiled separately.

Phase 19 verdict:

- Chapter 12 now starts correctly after Chapter 11.
- Chapter 12 completed end to end in the live browser.
- The support ladder was verified live on Level 4.
- The completion state persists after reloading the curriculum route.
- Class 3 English/Santoor now has authored Chapter 1-12 coverage in this rebuild flow, with all 12 completed in the dedicated live browser profile.

## Phase 20 - Class 4 Entry Slice Live QA

Live browser QA used:

```text
Chrome profile: Chrome-Zidd-SchoolPrep
CDP: http://127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
User: [SCHOOL_QA_ACCOUNT]
```

Runtime correction before testing:

```text
The built-in chrome-devtools connector was attached to the older career Chrome
instance on port 9222 and showed http://localhost:3000. Raw local CDP on 9225
was required for the school profile. Sandboxed localhost CDP calls failed with
EPERM, so the CDP probes used local-only unsandboxed commands.
```

Frontend server correction before testing:

```text
The existing localhost:3001 process was still proxying to BACKEND_INTERNAL_URL=http://127.0.0.1:8000.
Restarted localhost:3001 with:
NEXTAUTH_URL=http://localhost:3001
BACKEND_INTERNAL_URL=http://127.0.0.1:8088
NEXT_DIST_DIR=.next-schoolprep
```

Onboarding flow:

```text
/school/onboarding
Learner: Open Assets Learner
School: [QA_SCHOOL]
Class: Class 4
Subject: English
Teaching language: Hinglish
English comfort: medium
Focus signals: reading, grammar

POST /school/onboarding/complete -> 200 OK
```

Placement flow:

```text
/school
Class 4 - English
NEXT STEP
Start readiness check
START READINESS CHECK
```

Observed issue:

```text
The placement start card still said:
"The first questions check a few Class 2 and Class 3 English foundations..."
for a Class 4 learner.

Fixed in frontend: placement intro now uses the saved target class.
```

Class 4 placement items answered in browser:

```text
1. Understand unity words in a conversation
   passage: Mina said, "Our songs and foods are different..."
   answer: unity

2. Use context to understand a relationship word
   passage: trusted one another / bond grew stronger
   answer: trust

3. Find the main idea in a teamwork passage
   passage: reading corner jobs
   answer: teamwork

4. Explain why people help one another
   passage: Reva picked up the baton
   answer: helping each other

5. Suggest a fair solution in a group
   passage: two children wanted to speak first
   answer: listen to both

6. Use a collective noun
   passage: cows crossed the field
   answer: herd

7. Use but to show contrast
   prompt: Leena wanted to lead, ___ Arjun wanted to lead too.
   answer: but

8. Complete a meaningful sentence
   prompt: Good teammates ___ work fairly.
   answer: share
```

Placement final state:

```text
CONFIRMATION - 8/18
Readiness check saved
VIEW READINESS REPORT
```

Readiness report before fix:

```text
CLASS 4 FOUNDATIONS FIRST
You are ready to begin your target class chapters.
8/8 checks strong
Needs work: 0
Only Back button was visible.
```

Observed issue:

```text
Target-ready report was semantically contradictory and had no Start target class CTA.
```

Fixed in frontend:

```text
CLASS 4 TARGET CLASS READY
You are ready to begin your target class chapters.
8/8 checks strong
START TARGET CLASS
```

Curriculum landing:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 1 when you are ready.
START CHAPTER 1

Chapter map:
Chapter 1 Together We Can Ready
Chapter 2 Santoor Chapter 2 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 1 lesson start:

```text
Together We Can
Santoor - My Land
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / FIND THE MAIN IDEA IN A TEAMWORK PASSAGE
Learn: How teamwork solves a shared problem
```

Chapter 1 completed in browser:

```text
Level 1 - How teamwork solves a shared problem
guided answer: teamwork
independent answer: teamwork

Level 2 - Explain why helping matters
guided answer: Meera could get the ball safely
independent answer: she helped him find the library

Level 3 - Understand unity words
guided answer: unity
independent answer: unity

Level 4 - Use collective nouns
guided answer: herd
independent answer: swarm

Level 5 - Suggest a fair group solution
guided answer: listen to both
independent answer: take turns
```

Final state:

```text
Together We Can
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Phase 20 verdict:

- Class 4 onboarding works through the real browser profile.
- Class 4 authored placement starts and completes with target-ready evidence.
- Class 4 target-ready report now has the correct label and CTA.
- Class 4 curriculum landing exposes `Together We Can` as Chapter 1 and locks the remaining placeholder chapters.
- Class 4 Chapter 1 completed end to end in the live browser.
- Remaining UX/content caveat: Class 4 has only the first authored chapter in this entry slice; Chapters 2-12 remain placeholder/locked and must not be treated as complete Class 4 coverage.

## Phase 21 - Class 4 Chapter 2 Live Browser QA

Browser/profile:

```text
Chrome CDP: 127.0.0.1:9225
Chrome profile: Chrome-Zidd-SchoolPrep
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Account: [SCHOOL_QA_ACCOUNT]
```

Source map basis:

```text
NCERT Class 4 English Santoor Chapter 2: The Tinkling Bells
Structural source: https://ncert.nic.in/textbook/pdf/desa102.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 1 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 2 when you are ready.
START CHAPTER 2

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Ready
Chapter 3 Santoor Chapter 3 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 2 lesson start:

```text
The Tinkling Bells
Santoor - My Land
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / INFER HONEST ACTION FROM STORY CLUES
Learn: Choose the honest action
```

Chapter 2 browser completion path:

```text
Level 1 - Choose the honest action
guided answer: return the extra money
independent answer: return the extra money

Remediation observed:
An intentionally wrong independent answer sent the learner to BRIDGE SUPPORT.
Bridge answer: the extra money
The session then returned to the independent check instead of falsely advancing.

Level 2 - Put story events in order
guided answer: a shopkeeper gave extra change
independent answer: he received extra change

Level 3 - Use -er and -est comparisons
guided answer: smallest
independent answer: brighter

Level 4 - Choose opposite words
guided answer: ugly
independent answer: loudly

Level 5 - Write a careful sentence
guided answer: because
independent answer: I should return the extra change because it is not mine.
```

Final state:

```text
The Tinkling Bells
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Santoor Chapter 3 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Observed runtime/UI defect:

```text
The persisted completion map rendered correctly, but the page also showed:
"The server took too long to respond. Please try again."
This is a stale/incorrect error banner because the same screen had already loaded the successful completed state.
```

Phase 21 verdict:

- Raw CDP against the dedicated school Chrome profile worked on port 9225; the generic DevTools connector was not used for this run.
- Class 4 Chapter 2 starts from the real browser, serves the authored `The Tinkling Bells` lesson, and completes end to end.
- Bridge remediation works for a wrong independent answer and does not falsely mark the level complete.
- Persisted map correctly marks Chapters 1 and 2 complete and keeps Chapter 3+ locked.
- Remaining caveat: the frontend can show a stale timeout banner beside a successful completed curriculum state after reload. This must be fixed before treating the UI as polished.

## Phase 22 - Stale Timeout Banner Regression QA

Issue from Phase 21:

```text
The completed Class 4 curriculum map rendered correctly, but the page also showed:
"The server took too long to respond. Please try again."
```

Fix verified:

```text
The curriculum page now ignores stale load responses and clears old errors whenever a successful session or landing state is rendered.
Static guard added to scripts/check-school-rebuild-surface.mjs.
```

Live browser regression result:

```text
Chrome CDP: 127.0.0.1:9225
URL: http://localhost:3001/school/curriculum

CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Santoor Chapter 3 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasCompleted":true,"hasChapter1Complete":true,"hasChapter2Complete":true,"hasTimeout":false}
```

Phase 22 verdict:

- The stale timeout banner no longer appears beside a successful completed curriculum state.
- The completed Class 4 authored slice still persists correctly after reload.
- The remaining Class 4 scope caveat is content coverage, not this timeout UI defect: Chapters 3-12 are still locked placeholders.

## Phase 23 - Class 4 Chapter 3 Live Browser QA

Browser/profile:

```text
Chrome CDP: 127.0.0.1:9225
Chrome profile: Chrome-Zidd-SchoolPrep
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Account: [SCHOOL_QA_ACCOUNT]
```

Source map basis:

```text
NCERT Class 4 English Santoor Chapter 3: Be Smart, Be Safe
Structural source: https://ncert.nic.in/textbook/pdf/desa103.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 2 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 3 when you are ready.
START CHAPTER 3

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Ready
Chapter 4 Santoor Chapter 4 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 3 lesson start:

```text
Be Smart, Be Safe
Santoor - My Land
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / SEQUENCE SAFE ROAD-CROSSING STEPS
Learn: Cross the road carefully
```

Chapter 3 browser completion path:

```text
Level 1 - Cross the road carefully
guided answer: stop and look both ways
independent answer: look right left and right again

Level 2 - Sort safe and unsafe actions
guided answer: unsafe
independent answer: safe

Level 3 - Read traffic signs
guided answer: school ahead
independent answer: no honking

Level 4 - Count nouns correctly
guided answer: buses
independent answer: traffic

Level 5 - Write a safety promise
guided answer: because
independent answer: I will use the footpath because it keeps me away from traffic.
```

Final state:

```text
Be Smart, Be Safe
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 Santoor Chapter 4 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasCompleted":true,"hasChapter1Complete":true,"hasChapter2Complete":true,"hasChapter3Complete":true,"hasChapter4Locked":true,"hasTimeout":false}
```

Phase 23 verdict:

- Class 4 Chapter 3 starts from the real browser, serves the authored `Be Smart, Be Safe` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-3 complete and keeps Chapter 4+ locked.
- The stale timeout banner fixed in Phase 22 did not return during this Chapter 3 reload verification.
- Remaining Class 4 scope caveat: Chapters 4-12 are still locked placeholders and must not be treated as authored coverage.

## Phase 24 - Class 4 Chapter 4 Live Browser QA

Browser/profile:

```text
Chrome CDP: 127.0.0.1:9225
Chrome profile: Chrome-Zidd-SchoolPrep
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Account: [SCHOOL_QA_ACCOUNT]
```

Source map basis:

```text
NCERT Class 4 English Santoor Chapter 4: One Thing at a Time
Structural source: https://ncert.nic.in/textbook/pdf/desa104.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 3 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 4 when you are ready.
START CHAPTER 4

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Ready
Chapter 5 Santoor Chapter 5 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 4 lesson start:

```text
One Thing at a Time
Santoor - My Beautiful World
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / IDENTIFY THE MAIN MESSAGE OF A FOCUS POEM
Learn: Find the focus message
```

Chapter 4 browser completion path:

```text
Level 1 - Find the focus message
guided answer: one task at a time
independent answer: finish one task before starting another

Level 2 - Hear rhyme words
guided answer: day and way
independent answer: bright and right

Level 3 - Understand focus words
guided answer: strength
independent answer: short times

Level 4 - Use is/are with action words
guided answer: is reading
independent answer: are playing

Level 5 - Write a routine with order
guided answer: after
independent answer: I finish my homework before I play because one thing done well is better.
```

Final state:

```text
One Thing at a Time
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 Santoor Chapter 5 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasCompleted":true,"hasChapter1Complete":true,"hasChapter2Complete":true,"hasChapter3Complete":true,"hasChapter4Complete":true,"hasChapter5Locked":true,"hasTimeout":false}
```

Phase 24 verdict:

- Class 4 Chapter 4 starts from the real browser, serves the authored `One Thing at a Time` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-4 complete and keeps Chapter 5+ locked.
- The stale timeout banner fixed in Phase 22 did not return during this Chapter 4 reload verification.
- Remaining Class 4 scope caveat: Chapters 5-12 are still locked placeholders and must not be treated as authored coverage.

## Phase 25 - Class 4 Chapter 5 Live Browser QA

Browser/profile:

```text
Chrome CDP: 127.0.0.1:9225
Chrome profile: Chrome-Zidd-SchoolPrep
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Account: [SCHOOL_QA_ACCOUNT]
```

Runtime setup note:

```text
The first 3001 frontend restart used .env.local, which points BACKEND_INTERNAL_URL at http://127.0.0.1:8000 and NEXTAUTH_URL at http://localhost:3000.
That caused the live browser to read the wrong backend during QA. The frontend was restarted for this run with:
BACKEND_INTERNAL_URL=http://127.0.0.1:8088 NEXTAUTH_URL=http://localhost:3001 NEXT_DIST_DIR=.next-schoolprep-3001 npm run dev -- -p 3001
```

Source map basis:

```text
NCERT Class 4 English Santoor Chapter 5: The Old Stag
Structural source: https://ncert.nic.in/textbook/pdf/desa105.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 4 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 5 when you are ready.
START CHAPTER 5

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Ready
Chapter 6 Santoor Chapter 6 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 5 lesson start:

```text
The Old Stag
Santoor - My Beautiful World
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / INFER CHARACTER TRAITS FROM ACTIONS
Learn: Infer why kindness matters
```

Chapter 5 browser completion path:

```text
Level 1 - Infer why kindness matters
guided answer: kindness
independent answer: he cared for everyone

Level 2 - Use resources wisely
guided answer: leave grass for him
independent answer: share wisely

Level 3 - Read descriptive word groups
guided answer: tender
independent answer: shaded spot

Level 4 - Use adverbs of manner
guided answer: slowly
independent answer: carefully

Level 5 - Write a thank-you note
guided answer: because
independent answer: Thank you for bringing food because it helped me recover.
```

Final state:

```text
The Old Stag
Santoor - My Beautiful World
CLASS 4 - ENGLISH
5/5 levels complete
Good. This chapter level is complete, so the next level is ready.
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Santoor Chapter 6 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasCompleted":true,"hasChapter1Complete":true,"hasChapter2Complete":true,"hasChapter3Complete":true,"hasChapter4Complete":true,"hasChapter5Complete":true,"hasChapter6Locked":true,"hasTimeout":false,"has404":false}
```

Phase 25 verdict:

- Class 4 Chapter 5 starts from the real browser, serves the authored `The Old Stag` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-5 complete and keeps Chapter 6+ locked.
- The run confirmed the dedicated Chrome CDP profile works when Chrome is launched with `--remote-debugging-port=9225`.
- Local QA also exposed a setup risk: using the default frontend `.env.local` on port 3001 silently targets backend port 8000. SchoolPrep browser QA must override `BACKEND_INTERNAL_URL=http://127.0.0.1:8088` and `NEXTAUTH_URL=http://localhost:3001` until the local env setup is split cleanly.
- Remaining Class 4 scope caveat: Chapters 6-12 are still locked placeholders and must not be treated as authored coverage.

## Phase 26 - Class 4 Chapter 6 Live Browser QA

Browser/profile:

```text
Chrome CDP: 127.0.0.1:9225
Chrome profile: Chrome-Zidd-SchoolPrep
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Account: [SCHOOL_QA_ACCOUNT]
```

Runtime setup note:

```text
Frontend was running with the dedicated SchoolPrep runtime:
BACKEND_INTERNAL_URL=http://127.0.0.1:8088 NEXTAUTH_URL=http://localhost:3001 NEXT_DIST_DIR=.next-schoolprep-3001 npm run dev -- -p 3001
Backend was restarted on 8088 after the Chapter 6 code change.
```

Source map basis:

```text
NCERT Class 4 English Santoor Chapter 6: Braille
Structural source: https://ncert.nic.in/textbook/pdf/desa106.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 5 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 6 when you are ready.
START CHAPTER 6

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Ready
Chapter 7 Santoor Chapter 7 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 6 lesson start:

```text
Braille
Santoor - My Beautiful World
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / EXPLAIN HOW RAISED DOTS HELP READING
Learn: Understand reading by touch
```

Chapter 6 browser completion path:

```text
Level 1 - Understand reading by touch
guided answer: raised dots
independent answer: reading by touch

Level 2 - Explain an invention's purpose
guided answer: simplified it
independent answer: he made reading by touch easier

Level 3 - Use chapter vocabulary
guided answer: blacksmith
independent answer: invented

Level 4 - Read spl words
guided answer: splendid
independent answer: splash

Level 5 - Use was/were with action words
guided answer: The student was reading.
independent answer: were helping
```

Automation note:

```text
The first automated pass reached Level 5 but did not click the visible option because it searched for the partial text "was reading" while the UI option was "The student was reading.".
The learner-visible option was present and was clicked directly in the continuation pass. The independent check then completed normally.
```

Final state:

```text
Braille
Santoor - My Beautiful World
CLASS 4 - ENGLISH
5/5 levels complete
Good. This chapter level is complete, so the next level is ready.
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Santoor Chapter 7 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasCompleted":true,"hasChapter6Complete":true,"hasChapter7Locked":true,"hasTimeout":false,"has404":false}
```

Phase 26 verdict:

- Class 4 Chapter 6 starts from the real browser, serves the authored `Braille` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-6 complete and keeps Chapter 7+ locked.
- The Chapter 6 sequence exercised reading-by-touch comprehension, invention-purpose reasoning, vocabulary from context, `spl` words, and `was/were + -ing`.
- Remaining Class 4 scope caveat: Chapters 7-12 are still locked placeholders and must not be treated as authored coverage.

## Phase 27 - Class 4 Chapter 7 Live Browser QA

Browser/profile:

```text
Chrome CDP: 127.0.0.1:9225
Chrome profile: Chrome-Zidd-SchoolPrep
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Account: [SCHOOL_QA_ACCOUNT]
```

Runtime setup note:

```text
Frontend was running with the dedicated SchoolPrep runtime:
BACKEND_INTERNAL_URL=http://127.0.0.1:8088 NEXTAUTH_URL=http://localhost:3001 NEXT_DIST_DIR=.next-schoolprep-3001 npm run dev -- -p 3001
Backend was restarted on 8088 after the Chapter 7 code change.
```

Source map basis:

```text
NCERT Class 4 English Santoor Chapter 7: Fit Body, Fit Mind, Fit Nation
Structural source: https://ncert.nic.in/textbook/pdf/desa107.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 6 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 7 when you are ready.
START CHAPTER 7

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Ready
Chapter 8 Santoor Chapter 8 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 7 lesson start:

```text
Fit Body, Fit Mind, Fit Nation
Santoor - Fun with Games
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / CONNECT NAMES, GAMES, MUSIC, AND MOVEMENT CLUES
Learn: Find activity clues
```

Chapter 7 browser completion path:

```text
Level 1 - Find activity clues
guided answer: hockey
independent answer: music

Level 2 - Use describing words
guided answer: swift runner
independent answer: healthy food

Level 3 - Hear rhyme pairs
guided answer: race and pace
independent answer: joy and boy

Level 4 - Read double-letter words
guided answer: running
independent answer: balloon

Level 5 - Use fitness word meanings
guided answer: mistakes
independent answer: proudly
```

Final state:

```text
Fit Body, Fit Mind, Fit Nation
Santoor - Fun with Games
CLASS 4 - ENGLISH
5/5 levels complete
Good. This chapter level is complete, so the next level is ready.
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 Santoor Chapter 8 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasCompleted":true,"hasChapter7Complete":true,"hasChapter8Locked":true,"hasTimeout":false,"has404":false}
```

Phase 27 verdict:

- Class 4 Chapter 7 starts from the real browser, serves the authored `Fit Body, Fit Mind, Fit Nation` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-7 complete and keeps Chapter 8+ locked.
- The Chapter 7 sequence exercised activity comprehension, adjectives/describing words, rhyming words, double-letter spelling, and word meanings around effort/confidence/errors.
- Remaining Class 4 scope caveat: Chapters 8-12 are still locked placeholders and must not be treated as authored coverage.

## Phase 28 - Class 4 Chapter 8 Live Browser QA

Runtime setup:

```text
Browser: dedicated SchoolPrep Chrome profile on CDP 127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Account: [SCHOOL_QA_ACCOUNT]
Frontend command contract:
BACKEND_INTERNAL_URL=http://127.0.0.1:8088 NEXTAUTH_URL=http://localhost:3001 NEXT_DIST_DIR=.next-schoolprep-3001 npm run dev -- -p 3001
Backend was restarted on 8088 after the Chapter 8 code change.
```

Source map basis:

```text
NCERT Class 4 English Santoor Chapter 8: The Lagori Champions
Structural source: https://ncert.nic.in/textbook/pdf/desa108.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 7 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 8 when you are ready.
START CHAPTER 8

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Ready
Chapter 9 Santoor Chapter 9 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 8 lesson start:

```text
The Lagori Champions
Santoor - Fun with Games
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / READ RULE CLUES IN A DIALOGUE
Learn: Understand game rules
```

Chapter 8 browser completion path:

```text
Level 1 - Understand game rules
guided answer: seven stones
independent answer: stack and avoid the ball

Level 2 - Track match sequence
guided answer: referee blew the whistle
independent answer: Prakash set the seventh stone

Level 3 - Use match vocabulary
guided answer: opponent
independent answer: boundary

Level 4 - Build clear sentences
guided answer: The field is marked with a boundary.
independent answer: Everybody looked at Prakash with surprise.

Level 5 - Tell sentence from question
guided answer: question
independent answer: sentence
```

Final state:

```text
The Lagori Champions
Santoor - Fun with Games
CLASS 4 - ENGLISH
5/5 levels complete
Good. This chapter level is complete, so the next level is ready.
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Santoor Chapter 9 Locked
...
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasChapter8Complete":true,"hasChapter9Locked":true,"hasAllAvailable":true,"hasTimeout":false,"has404":false}
```

Phase 28 verdict:

- Class 4 Chapter 8 starts from the real browser, serves the authored `The Lagori Champions` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-8 complete and keeps Chapter 9+ locked.
- The Chapter 8 sequence exercised traditional-game rule comprehension, event sequencing, match vocabulary, sentence order, and sentence-vs-question classification.
- Remaining Class 4 scope caveat: Chapters 9-12 are still locked placeholders and must not be treated as authored coverage.

## Phase 29 - Class 4 Chapter 9 Live Browser QA

Runtime setup:

```text
Browser: dedicated SchoolPrep Chrome profile on CDP 127.0.0.1:9225
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Account: [SCHOOL_QA_ACCOUNT]
Frontend command contract:
BACKEND_INTERNAL_URL=http://127.0.0.1:8088 NEXTAUTH_URL=http://localhost:3001 NEXT_DIST_DIR=.next-schoolprep-3001 npm run dev -- -p 3001
Backend was restarted on 8088 after the Chapter 9 code change.
```

Source map basis:

```text
NCERT Class 4 English Santoor Chapter 9: Hekko
Structural source: https://ncert.nic.in/textbook/pdf/desa109.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 8 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 9 when you are ready.
START CHAPTER 9

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Hekko Ready
Chapter 10 Santoor Chapter 10 Locked
Chapter 11 Santoor Chapter 11 Locked
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 9 lesson start:

```text
Hekko
Santoor - Fun with Games
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / USE WORD PARTS AND STORY CONTEXT
Learn: Understand Hekko's name
```

Chapter 9 browser completion path:

```text
Level 1 - Understand Hekko's name
guided answer: challenging the tiger
independent answer: challenge

Level 2 - Read team rules
guided answer: 11
independent answer: human chain

Level 3 - Understand surrender and scoring
guided answer: surrender
independent answer: the game ends

Level 4 - Choose sound-alike words
guided answer: There
independent answer: their

Level 5 - Use simple past verbs
guided answer: visited
independent answer: decided
```

Final state:

```text
Hekko
Santoor - Fun with Games
CLASS 4 - ENGLISH
5/5 levels complete
Good. This chapter level is complete, so the next level is ready.
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Hekko Complete
Chapter 10 Santoor Chapter 10 Locked
Chapter 11 Santoor Chapter 11 Locked
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasChapter9Complete":true,"hasChapter10Locked":true,"hasAllAvailable":true,"hasTimeout":false,"has404":false}
```

Phase 29 verdict:

- Class 4 Chapter 9 starts from the real browser, serves the authored `Hekko` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-9 complete and keeps Chapter 10+ locked.
- The Chapter 9 sequence exercised cultural word meaning, team-rule comprehension, surrender/end-condition reasoning, homophones, and simple past tense.
- Remaining Class 4 scope caveat: Chapters 10-12 are still locked placeholders and must not be treated as authored coverage.

## Phase 30 - Class 4 Chapter 10 `The Swing`

Runtime:

```text
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Browser: Chrome CDP on http://127.0.0.1:9225
Profile: /Users/18abhinav07/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

Source-map basis:

```text
NCERT Class 4 English Santoor Chapter 10: The Swing
Structural source: https://ncert.nic.in/textbook/pdf/desa110.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 9 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Hekko Complete
Chapter 10 The Swing Ready
Chapter 11 Santoor Chapter 11 Locked
Chapter 12 Santoor Chapter 12 Locked
```

Chapter 10 lesson start:

```text
The Swing
Santoor - Up High
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / READ VISUAL CLUES IN A POEM
Learn: Notice views from above
```

Chapter 10 browser completion path:

```text
Level 1 - Notice views from above
guided answer: rivers and trees
independent answer: garden green

Level 2 - Infer the speaker's feeling
guided answer: pleasantest thing
independent answer: he enjoys swinging

Level 3 - Stretch a sentence
guided answer: Mira watched the clouds
independent answer: Mira watched the clouds from the swing.

Level 4 - Tell noun from verb
guided answer: verb
independent answer: noun

Level 5 - Use position words
guided answer: between
independent answer: under
```

Final state:

```text
The Swing
Santoor - Up High
CLASS 4 - ENGLISH
5/5 levels complete
Good. This chapter level is complete, so the next level is ready.
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Hekko Complete
Chapter 10 The Swing Complete
Chapter 11 Santoor Chapter 11 Locked
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasChapter10Complete":true,"hasChapter11Locked":true,"hasAllAvailable":true,"hasTimeout":false,"has404":false}
```

Phase 30 verdict:

- Class 4 Chapter 10 starts from the real browser, serves the authored `The Swing` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-10 complete and keeps Chapters 11-12 locked.
- The Chapter 10 sequence exercised poem visual clues, feeling inference, sentence expansion, noun/verb usage, and prepositions.
- Remaining Class 4 scope caveat: Chapters 11-12 are still locked placeholders and must not be treated as authored coverage.

## Phase 31 - Class 4 Chapter 11 `A Journey to the Magical Mountains`

Runtime:

```text
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Browser: Chrome CDP on http://127.0.0.1:9225
Profile: /Users/18abhinav07/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

Source-map basis:

```text
NCERT Class 4 English Santoor Chapter 11: A Journey to the Magical Mountains
Structural source: https://ncert.nic.in/textbook/pdf/desa111.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 10 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 11 when you are ready.
START CHAPTER 11

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Hekko Complete
Chapter 10 The Swing Complete
Chapter 11 A Journey to the Magical Mountains Ready
Chapter 12 Santoor Chapter 12 Locked
```

Observed start handoff:

```text
/school
NEXT STEP
Continue class
Open Assets Learner, continue Class 4 English: A Journey to the Magical Mountains.
The learner is now working inside the target-class teaching loop.
CONTINUE CLASS
```

Chapter 11 lesson start:

```text
A Journey to the Magical Mountains
Santoor - Up High
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / SEQUENCE STORY EVENTS AND PLACES
Learn: Track the journey setting
```

Chapter 11 browser completion path:

```text
Level 1 - Track the journey setting
guided answer: Himalayas
independent answer: river

Level 2 - Use mountain words in context
guided answer: Sherpa
independent answer: journey

Level 3 - Connect animals and care for nature
guided answer: milk, wool, and carrying loads
independent answer: protect the mountains

Level 4 - Understand body-part comparisons
guided answer: foot
independent answer: mouth

Level 5 - Join ideas with conjunctions
guided answer: because
independent answer: but
```

Final state:

```text
A Journey to the Magical Mountains
Santoor - Up High
CLASS 4 - ENGLISH
5/5 levels complete
Good. This chapter level is complete, so the next level is ready.
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Hekko Complete
Chapter 10 The Swing Complete
Chapter 11 A Journey to the Magical Mountains Complete
Chapter 12 Santoor Chapter 12 Locked
```

Assertion summary:

```json
{"hasChapter11Complete":true,"hasChapter12Locked":true,"hasAllAvailable":true,"hasTimeout":false,"has404":false}
```

Phase 31 verdict:

- Class 4 Chapter 11 starts from the real browser, serves the authored `A Journey to the Magical Mountains` lesson, and completes end to end.
- The `/school` shell correctly resumes the newly started Chapter 11 session through `Continue class`.
- The persisted map correctly marks Chapters 1-11 complete and keeps Chapter 12 locked.
- The Chapter 11 sequence exercised story sequence, mountain vocabulary, animals-and-care reasoning, body-part metaphors, and conjunctions.
- Remaining Class 4 scope caveat: Chapter 12 is still a locked placeholder and must not be treated as authored coverage.

## Phase 32 - Class 4 Chapter 12 `Maheshwar`

Runtime:

```text
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Browser: Chrome CDP on http://127.0.0.1:9225
Profile: /Users/18abhinav07/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

Source-map basis:

```text
NCERT Class 4 English Santoor Chapter 12: Maheshwar
Structural source: https://ncert.nic.in/textbook/pdf/desa112.pdf
Runtime content policy: Zidd-authored original passages, prompts, options, and answer keys. No NCERT body text is served.
```

Initial landing after Class 4 Chapter 11 completion:

```text
/school/curriculum
CLASS 4 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 12 when you are ready.
START CHAPTER 12

Chapter map:
Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Hekko Complete
Chapter 10 The Swing Complete
Chapter 11 A Journey to the Magical Mountains Complete
Chapter 12 Maheshwar Ready
```

Chapter 12 lesson start:

```text
Maheshwar
Santoor - Up High
CLASS 4 - ENGLISH
0/5 levels complete

GUIDED CHECK / FIND WHO AND WHERE DETAILS
Learn: Read facts in a dialogue
```

Chapter 12 browser completion path:

```text
Level 1 - Read facts in a dialogue
guided answer: Queen Ahilya Bai
independent answer: Narmada River

Level 2 - Identify fort features
guided answer: overhanging balconies
independent answer: red stones

Level 3 - Find the odd word out
guided answer: thrilled
independent answer: kind

Level 4 - Spot silent g words
guided answer: sign
independent answer: design

Level 5 - Choose a, an, or the
guided answer: an
independent answer: the
```

Final state:

```text
Maheshwar
Santoor - Up High
CLASS 4 - ENGLISH
5/5 levels complete
Good. This chapter level is complete, so the next level is ready.
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Complete
Level 2 Complete
Level 3 Complete
Level 4 Complete
Level 5 Complete
```

Persisted chapter map after reload:

```text
CLASS 4 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Together We Can Complete
Chapter 2 The Tinkling Bells Complete
Chapter 3 Be Smart, Be Safe Complete
Chapter 4 One Thing at a Time Complete
Chapter 5 The Old Stag Complete
Chapter 6 Braille Complete
Chapter 7 Fit Body, Fit Mind, Fit Nation Complete
Chapter 8 The Lagori Champions Complete
Chapter 9 Hekko Complete
Chapter 10 The Swing Complete
Chapter 11 A Journey to the Magical Mountains Complete
Chapter 12 Maheshwar Complete
```

Assertion summary:

```json
{"hasChapter12Complete":true,"hasAllAvailable":true,"hasAnyLocked":false,"completeMatches":12,"hasTimeout":false,"has404":false}
```

Phase 32 verdict:

- Class 4 Chapter 12 starts from the real browser, serves the authored `Maheshwar` lesson, and completes end to end.
- The persisted map correctly marks all 12 Class 4 chapters complete.
- The Chapter 12 sequence exercised dialogue facts, fort features, synonym odd-one-out, silent `g`, and articles.
- Remaining Class 4 scope caveat: no locked Class 4 chapter placeholders remain in the current learner map.

## Phase 33 - Class 5 Chapter 1 `Papa's Spectacles`

Runtime:

```text
Date: 2026-07-11 15:41 IST
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Chrome CDP: raw CDP on 127.0.0.1:9225
Chrome profile: ~/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

CDP target verification:

```text
The generic DevTools MCP listed only http://localhost:3000/map, so it was attached
to the older career-prep browser target. Raw CDP on 9225 listed the dedicated
school-prep page:

http://localhost:3001/school/curriculum
ws://127.0.0.1:9225/devtools/page/BFEB8571B1A31C5B59A2FF9F5A1E792F
```

Official source used:

```text
NCERT selector: https://ncert.nic.in/textbook.php
Class 5 English: Santoor
Book code: eesa1
Chapter 1 PDF: https://ncert.nic.in/textbook/pdf/eesa101.pdf
Chapter title from PDF: Papa's Spectacles
Unit: Let's Have Fun
```

Browser onboarding path:

```text
School setup
Learner: Open Assets Learner
School: Open Assets Test School
Class: Class 5
Subject: English
Teaching language: Hinglish
English comfort: medium
Focus signals: reading, vocabulary
```

Placement flow:

```text
Readiness check ready state:
Start your first snapshot
The first questions check English foundations needed for Class 5 with visible context.

First rendered item:
SNAPSHOT - 0/18
Find a clear story detail
Papa looked in his pockets, under the chair, and near the window because he had lost his spectacles.
What was Papa searching for?
```

Placement answer transcript:

```text
snapshot: spectacles
snapshot: looked quickly
snapshot: vegetables
snapshot: cherry
snapshot: on his head
snapshot: shoes
snapshot: around
snapshot: father is unhappy
confirmation: spectacles
confirmation: head
confirmation: looking for
confirmation: socks
confirmation: spectacles
confirmation: on
confirmation: handkerchief
confirmation: he lost his spectacles
```

Readiness report:

```text
CLASS 5 TARGET CLASS READY
You are ready to begin your target class chapters.
Placement evidence shows the learner can start target-class work.
16/16 checks strong
Needs work 0
START TARGET CLASS
```

Initial Class 5 curriculum map:

```text
CLASS 5 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 1 when you are ready.

Chapter 1 Papa's Spectacles Ready
Chapter 2 Santoor Chapter 2 Locked
Chapter 3 Santoor Chapter 3 Locked
Chapter 4 Santoor Chapter 4 Locked
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Chapter 1 browser completion path:

```text
Level 1 - Track the story detail
guided answer: spectacles
independent answer: on his head

Level 2 - Use chapter words in context
guided answer: eyeglasses
independent answer: looked quickly

Level 3 - Order words by size
guided answer: handkerchief
independent answer: cherry

Level 4 - Use pair phrases
guided answer: shoes
independent answer: socks

Level 5 - Choose location words
guided answer: around
independent answer: on
```

Final chapter state:

```text
Papa's Spectacles
Santoor - Let's Have Fun
CLASS 5 - ENGLISH
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Track the story detail Complete
Level 2 Use chapter words in context Complete
Level 3 Order words by size Complete
Level 4 Use pair phrases Complete
Level 5 Choose location words Complete
```

Persisted map after refresh:

```text
CLASS 5 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Papa's Spectacles Complete
Chapter 2 Santoor Chapter 2 Locked
Chapter 3 Santoor Chapter 3 Locked
Chapter 4 Santoor Chapter 4 Locked
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Phase 33 verdict:

- Class 5 onboarding, placement, readiness report, target-class unlock, Chapter 1 start, Chapter 1 completion, and persisted map were verified through the dedicated Chrome profile on CDP `9225`.
- Class 5 Chapter 1 serves the authored `Papa's Spectacles` lesson and completes end to end.
- Chapter 2 remains locked because it is not authored yet, so the UI does not falsely expose unsupported content as teachable.
- QA note: CDP automation exposed sluggish async feedback on option-click questions; repeated clicks during a pending request were harmless/idempotent, but the UI should make pending state clearer before broader learner testing.

## Phase 34 - Class 5 Chapter 2 `Gone with the Scooter`

Runtime:

```text
Date: 2026-07-11 15:52 IST
Frontend: http://localhost:3001
Backend: http://127.0.0.1:8088
Chrome CDP: raw CDP on 127.0.0.1:9225
Chrome profile: ~/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

Official source used:

```text
NCERT selector: https://ncert.nic.in/textbook.php
Class 5 English: Santoor
Book code: eesa1
Chapter 2 PDF: https://ncert.nic.in/textbook/pdf/eesa102.pdf
Chapter title from PDF: Gone with the Scooter
Unit: Let's Have Fun
PDF metadata: 16 pages, modified 2026-03-24
```

Initial Class 5 curriculum map after backend restart:

```text
CLASS 5 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 2 when you are ready.

Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Ready
Chapter 3 Santoor Chapter 3 Locked
Chapter 4 Santoor Chapter 4 Locked
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Chapter 2 first rendered lesson:

```text
Gone with the Scooter
Santoor - Let's Have Fun
CLASS 5 - ENGLISH
0/5 levels complete

Learn: Sequence the story event
A sequence answer follows what happens first, next, and last.
Gopi heard a thud, searched the garden, and found a hard white hockey ball near dry leaves.
What did Gopi find in the garden?
```

Chapter 2 browser completion path:

```text
Level 1 - Sequence the story event
guided answer: hockey ball
independent answer: scooter basket

Level 2 - Judge ownership clues
guided answer: four months ago
independent answer: ask around

Level 3 - Understand action words
guided answer: small taps
independent answer: take suddenly

Level 4 - Join event ideas
guided answer: because
independent answer: however

Level 5 - Hear long oo and build words
guided answer: school
independent answer: football
```

Final chapter state:

```text
Gone with the Scooter
Santoor - Let's Have Fun
CLASS 5 - ENGLISH
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Sequence the story event Complete
Level 2 Judge ownership clues Complete
Level 3 Understand action words Complete
Level 4 Join event ideas Complete
Level 5 Hear long oo and build words Complete
```

Persisted map after refresh:

```text
CLASS 5 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 Santoor Chapter 3 Locked
Chapter 4 Santoor Chapter 4 Locked
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Phase 34 verdict:

- Class 5 Chapter 2 starts from the real browser, serves the authored `Gone with the Scooter` lesson, and completes end to end.
- The persisted map correctly marks Chapters 1-2 complete and keeps unauthored Chapters 3-10 locked.
- The Chapter 2 sequence exercised story sequencing, ownership/fairness inference, sports action vocabulary, connectors, long `oo`, and compound words.

## Phase 35 - Class 5 Chapter 3 `The Rainbow`

Historical note: this was the first five-level slice. The reviewer found material pedagogy and grading gaps; Phase 36 supersedes it with the current 11-level chapter and fresh browser evidence.

Runtime:

```text
Date: 2026-07-11 16:36 IST
Frontend: http://localhost:3001 via npm run dev:school-prep
Backend: http://127.0.0.1:8088
Chrome CDP: raw CDP on 127.0.0.1:9225
Chrome profile: ~/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

Official source used:

```text
NCERT selector: https://ncert.nic.in/textbook.php
Class 5 English: Santoor
Book code: eesa1
Selector entry: eesa1=3-10
Chapter 3 PDF: https://ncert.nic.in/textbook/pdf/eesa103.pdf
Chapter title from PDF: The Rainbow
Unit: My Colourful World
```

Initial Class 5 curriculum map after refresh:

```text
CLASS 5 - ENGLISH
Santoor
Target class is unlocked. Start Chapter 3 when you are ready.

Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Ready
Chapter 4 Santoor Chapter 4 Locked
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Chapter 3 first rendered lesson:

```text
The Rainbow
Santoor - My Colourful World
CLASS 5 - ENGLISH
0/5 levels complete

Learn: Picture the poem image
The poem asks us to picture a rainbow as a bright bridge across the sky.
What is the bright arc in the sky?
Options: rainbow, boat, road, river
```

Chapter 3 browser completion path:

```text
Level 1 - Picture the poem image
guided answer: rainbow
independent answer: rainbow

Level 2 - Use context for poem words
guided answer: over
independent answer: bridge

Level 3 - Hear rhyme in poem lines
guided answer: rain
independent answer: sky

Level 4 - Build compound words
guided answer: rainbow
independent answer: teacup

Level 5 - Write about a journey
guided answer: past tense
independent answer: I travelled by bus with my family.
```

The initial bulk CDP sequence advanced faster than the rendered activity could settle and produced wrong attempts in Levels 1-2. The live learner flow recovered through its bridge/retry states, and the remainder was completed with one visible action followed by a settled-DOM check before the next action. No answer endpoint was called directly.

Final chapter state:

```text
The Rainbow
Santoor - My Colourful World
CLASS 5 - ENGLISH
5/5 levels complete
Chapter complete.
Zidd saved the chapter evidence. All available authored chapters are complete for this slice.
ALL AVAILABLE CHAPTERS COMPLETE

Level 1 Picture the poem image Complete
Level 2 Use context for poem words Complete
Level 3 Hear rhyme in poem lines Complete
Level 4 Build compound words Complete
Level 5 Write about a journey Complete
```

Persisted map after restarting the intended School Prep frontend runtime and refreshing the browser:

```text
CLASS 5 - ENGLISH
Santoor
All available target-class chapters are complete.
ALL AVAILABLE CHAPTERS COMPLETE

Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Complete
Chapter 4 Santoor Chapter 4 Locked
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Runtime diagnostic note:

- A generic `npm run dev -- --port 3001` restart briefly pointed the frontend at backend `8000` and OAuth origin `3000`, producing a false reset-looking map and a transient NextAuth bundle error.
- Restarting with the dedicated `npm run dev:school-prep` command restored backend `8088`, OAuth origin `3001`, and the isolated `.next-schoolprep-3001` directory. The persisted map then correctly showed Chapters 1-3 complete.

Phase 35 verdict:

- Class 5 Chapter 3 starts from the real authenticated browser, serves the original Zidd-authored `The Rainbow` teaching sequence, and completes end to end.
- The persisted map correctly marks Chapters 1-3 complete and keeps unauthored Chapters 4-10 locked.
- The sequence covers poem imagery, vocabulary in context, rhyme, compound words, and a short past-tense journey sentence.
- Browser automation must wait for each backend-backed activity transition before submitting the next answer. The existing `submitting` disabled state protects ordinary learner interaction, but the QA runner should retain one-action/settled-state sequencing.

## Phase 36 - Reviewed and expanded Class 5 Chapter 3

Runtime:

```text
Date: 2026-07-11 17:00 IST
Frontend: http://localhost:3001 via npm run dev:school-prep
Backend: http://127.0.0.1:8088
Chrome CDP: raw CDP on 127.0.0.1:9225
Chrome profile: ~/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

Review findings remediated:

- Replaced fixed-example grading for the open journey task with deterministic structural rules.
- Added negation-aware phrase matching so responses such as `not a rainbow` and `not past tense` do not pass because they contain a keyword.
- Reworked Level 1 so the independent check explains the bridge comparison instead of merely naming a rainbow.
- Replaced the repeated `tea + cup` independent item with a distinct `wrist + watch` check.
- Added a versioned completion contract so a materially revised chapter reopens without erasing valid earlier-chapter progress.
- Replaced the single-sentence endpoint as the final writing outcome with a separate 80-100 word journey paragraph and a multiline browser input.

Official learning surface used as the structural map:

```text
Poem image and bridge comparison
Reference words across stanzas
Chapter vocabulary in context
Rhyme by sound
Compound words
Words used as nouns and verbs
Opposites in context
Journey planning and past tense
80-100 word journey paragraph
VIBGYOR colour order
Natural and human-made comparison
```

Version-migration state before restart:

```text
Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Complete (historical five-level completion)
```

Persisted state after the revised backend restarted:

```text
Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Ready
Chapter 4 Santoor Chapter 4 Locked
```

This proves content versioning reopened only the revised chapter while preserving valid Chapter 1-2 evidence.

First rendered current-build lesson:

```text
The Rainbow
Santoor - My Colourful World
CLASS 5 - ENGLISH
0/11 levels complete

GUIDED CHECK
EXPLAIN WHY THE RAINBOW IS COMPARED WITH A BRIDGE

A poem image lets you see an idea in your mind. The colourful arc is compared with a bridge because it seems to stretch from the ground towards the sky.

After rain, colours curved above the trees and looked like a path joining the earth and sky.

What does the colourful arc seem to form?
```

Current chapter map inside the session:

```text
Level 1 Picture the poem image
Level 2 Use context for poem words
Level 3 Track what reference words mean
Level 4 Hear rhyme in poem lines
Level 5 Build compound words
Level 6 Use one word in two jobs
Level 7 Build meaning with opposites
Level 8 Plan a journey paragraph
Level 9 Write a complete journey paragraph
Level 10 Order the rainbow colours
Level 11 Compare natural and human-made crossings
```

Browser completion path:

```text
1. bridge comparison guided -> independent -> 1/11
2. context vocabulary guided -> independent -> 2/11
3. reference words guided -> independent -> 3/11
4. rhyme guided -> independent -> 4/11
5. compound words guided -> independent -> 5/11
6. noun/verb use guided -> independent -> 6/11
7. opposites guided -> independent -> 7/11
8. journey planning guided -> independent -> 8/11
9. journey paragraph guided -> 80-word textarea response -> 9/11
10. VIBGYOR guided -> independent -> 10/11
11. natural/human-made guided -> independent -> 11/11
```

The browser runner interacted only with visible options, input fields, the multiline textarea, and submit buttons. It waited for the rendered activity to change after every answer and did not call an answer endpoint directly.

Final current-build chapter state:

```text
The Rainbow
Santoor - My Colourful World
CLASS 5 - ENGLISH
11/11 levels complete
Chapter complete.

Level 1 Picture the poem image Complete
Level 2 Use context for poem words Complete
Level 3 Track what reference words mean Complete
Level 4 Hear rhyme in poem lines Complete
Level 5 Build compound words Complete
Level 6 Use one word in two jobs Complete
Level 7 Build meaning with opposites Complete
Level 8 Plan a journey paragraph Complete
Level 9 Write a complete journey paragraph Complete
Level 10 Order the rainbow colours Complete
Level 11 Compare natural and human-made crossings Complete
```

Persisted map after completion:

```text
CLASS 5 - ENGLISH
Santoor
All available target-class chapters are complete.

Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Complete
Chapter 4 Santoor Chapter 4 Locked
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Phase 36 verdict:

- The current Chapter 3 payload was rendered and completed in the authenticated browser after the review fixes and backend restart.
- The chapter now covers the official core learning surface with original Zidd-authored teaching text and checks rather than a five-level summary.
- The open writing outcome uses a real multiline response, an 80-100 word requirement, past-tense evidence, and journey-detail evidence.
- Material content revisions reopen only the affected chapter, preserving earlier completed chapters.
- Chapter 4 remains locked because it is not authored yet.

## Phase 37 - Adversarial paragraph grading and bridge recovery

Runtime:

```text
Date: 2026-07-11 17:21 IST
Frontend: http://localhost:3001 via npm run dev:school-prep
Backend: http://127.0.0.1:8088
Chrome CDP: raw CDP on 127.0.0.1:9225
Chrome profile: ~/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

Reviewer bypasses reproduced before the fix:

```text
I do not believe this is a rainbow
```

The phrase matcher previously accepted the distant `rainbow` keyword even though it was negated.

```text
I went bus I went bus ... repeated to 81 words
```

The first paragraph rule previously accepted this because it counted duplicate past verbs and did not require sentence or experience structure.

Post-fix certification requirements:

```text
80-100 words
at least four complete sentences
at least 30 distinct normalized words
at least three distinct past-tense actions
travel context
time context
companion context
reflection or feeling evidence
```

The phrase matcher now rejects a matched phrase when a negation appears earlier in the answer. This is intentionally conservative for certifying checks.

Browser recertification sequence:

```text
Content version changed from 2026-07-11.2 to 2026-07-11.3.
Chapter 1 Papa's Spectacles remained Complete.
Chapter 2 Gone with the Scooter remained Complete.
Chapter 3 The Rainbow reopened as Ready.
```

The browser completed Levels 1-8 and reached the Level 9 independent paragraph textarea at `8/11 levels complete`.

Adversarial browser submission:

```text
Input type: visible textarea
Input length: 81 words
Input: repeated "I went bus"
Result: rejected
Next activity: BRIDGE SUPPORT / Write a complete journey paragraph
Progress: remained 8/11
```

Rendered bridge:

```text
Bridge support: order the paragraph as beginning, journey details, memorable moment, and ending feeling.

We reached the lake. We travelled by bus. I felt peaceful. Last Sunday we left home early.

Which sentence should begin the paragraph?
```

The browser then selected `Last Sunday we left home early.`, returned to the independent paragraph, submitted the valid original 80-word journey response, and completed Levels 10-11.

Final browser state:

```text
The Rainbow
CLASS 5 - ENGLISH
11/11 levels complete
Chapter complete.
```

Persisted map after `REFRESH PATH`:

```text
Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Complete
Chapter 4 Santoor Chapter 4 Locked
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Additional browser finding and fix:

- The first rejected independent paragraph rendered revision-level wording even though the next activity was a bridge.
- `_feedback_message()` now returns `Not yet. Zidd will slow this chapter level down with a bridge check.` for independent-to-bridge transitions.
- A dedicated regression test locks this learner-facing transition copy.

Phase 37 verdict:

- Repetitive word salad no longer creates false writing evidence.
- Distant negation no longer creates false short-answer evidence.
- A failed paragraph opens focused bridge support without advancing the level.
- A valid structured paragraph can recover from the bridge and complete the level.
- Versioned recertification preserves valid earlier chapters and persists the revised Chapter 3 completion.

## Phase 38 - Class 5 Chapter 4 `The Wise Parrot`

Runtime:

```text
Date: 2026-07-11 17:35 IST
Frontend: http://localhost:3001 via npm run dev:school-prep
Backend: http://127.0.0.1:8088
Chrome CDP: raw CDP on 127.0.0.1:9225
Chrome profile: ~/Library/Application Support/Google/Chrome-Zidd-SchoolPrep
User: [SCHOOL_QA_ACCOUNT]
```

Official source used:

```text
NCERT selector: https://ncert.nic.in/textbook.php
Class 5 English: Santoor
Book code: eesa1
Selector entry: eesa1=4-10
Chapter 4 PDF: https://ncert.nic.in/textbook/pdf/eesa104.pdf
Chapter title: The Wise Parrot
Unit: My Colourful World
```

Official core learning surface used as the structural map:

```text
Story sequence and escape inference
Freedom, wisdom, and intelligence reasoning
Chapter words and phrases in context
Collective nouns
Present perfect with has/have
Informational reading about safe bird habitats
ai and oi sound distinction
Opinion with evidence
Original story continuation
Bird-feeder procedure and safety
```

Initial Class 5 map:

```text
Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Complete
Chapter 4 The Wise Parrot Ready
Chapter 5 Santoor Chapter 5 Locked
```

First rendered current-build lesson:

```text
The Wise Parrot
Santoor - My Colourful World
CLASS 5 - ENGLISH
0/10 levels complete

GUIDED CHECK
SEQUENCE THE MESSAGE, IMITATION, AND ESCAPE
Learn: Follow the escape plan

A story sequence connects what happened first, what changed, and what happened because of it.

A trader agreed to carry his caged bird's greeting to wild parrots in a distant forest.

What did the trader carry to the forest parrots?
```

Rendered chapter map:

```text
Level 1 Follow the escape plan
Level 2 Reason about freedom and wisdom
Level 3 Use story words and phrases
Level 4 Name groups precisely
Level 5 Connect past actions to now
Level 6 Read about safe bird habitats
Level 7 Hear ai and oi clearly
Level 8 Give an opinion with evidence
Level 9 Continue the parrot's story
Level 10 Plan a safe bird feeder
```

Browser completion path:

```text
1. story sequence guided -> independent -> 1/10
2. freedom and wisdom guided -> independent -> 2/10
3. words and phrases guided -> independent -> 3/10
4. collective nouns guided -> independent -> 4/10
5. present perfect guided -> independent -> 5/10
6. safe bird habitats guided -> independent -> 6/10
7. ai/oi sounds guided -> independent -> 7/10
8. opinion and reason guided -> independent -> 8/10
9. story continuation guided -> 76-word textarea response -> 9/10
10. bird-feeder procedure guided -> independent -> 10/10
```

The browser runner interacted only with visible options, inputs, the multiline textarea, and submit buttons. It waited for every rendered activity transition and did not call an answer endpoint directly.

Final browser state:

```text
The Wise Parrot
Santoor - My Colourful World
CLASS 5 - ENGLISH
10/10 levels complete
Chapter complete.

Level 1 Follow the escape plan Complete
Level 2 Reason about freedom and wisdom Complete
Level 3 Use story words and phrases Complete
Level 4 Name groups precisely Complete
Level 5 Connect past actions to now Complete
Level 6 Read about safe bird habitats Complete
Level 7 Hear ai and oi clearly Complete
Level 8 Give an opinion with evidence Complete
Level 9 Continue the parrot's story Complete
Level 10 Plan a safe bird feeder Complete
```

Persisted map after `REFRESH PATH`:

```text
Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Complete
Chapter 4 The Wise Parrot Complete
Chapter 5 Santoor Chapter 5 Locked
Chapter 6 Santoor Chapter 6 Locked
Chapter 7 Santoor Chapter 7 Locked
Chapter 8 Santoor Chapter 8 Locked
Chapter 9 Santoor Chapter 9 Locked
Chapter 10 Santoor Chapter 10 Locked
```

Phase 38 verdict:

- Chapter 4 starts from the real authenticated browser and serves the current 10-level authored payload.
- The long-form story continuation renders in the multiline writing control and completes under the 60-90 word structural contract.
- The module connects story comprehension, grammar, vocabulary, sound, opinion, writing, and practical bird care instead of reducing the chapter to a short quiz.
- Progress persists after returning to the chapter map.
- Chapter 5 remains locked because it is not authored yet.

## Phase 39 - Evidence-backed writing evaluation and timeout recovery

Date: 2026-07-11

This phase retested the reviewed Chapter 3/4 grading changes through the same
authenticated Chrome profile. It supersedes Phase 38's structural-only claim
for long writing; long answers now require a strict rubric evaluation after a
deterministic structural preflight.

Version migration after a hard reload behaved correctly:

```text
Chapter 1 Papa's Spectacles Complete
Chapter 2 Gone with the Scooter Complete
Chapter 3 The Rainbow Ready
Chapter 4 The Wise Parrot Locked
```

Only the revised chapters reopened. Earlier valid chapter completions remained
intact.

Chapter 3 adversarial and recovery evidence:

```text
81-word repeated "I went bus" answer -> rejected
model call -> skipped by structural preflight
next activity -> Bridge: Write a complete journey paragraph
visible request duration -> 5,001 ms
```

The bridge answer returned the learner to the independent writing check. A
valid 80-word journey paragraph then exposed a production-significant defect in
the original synchronous integration:

```text
browser request duration -> 21,008 ms
frontend result -> request_timeout
visible message -> The server took too long to respond. Please try again.
backend result after browser timeout -> 200
persisted state after reload -> paragraph accepted, Chapter 3 advanced to 9/11
```

That was an ambiguous late commit: the learner was told to retry even though
the server had already advanced. The following fixes were then implemented:

- an 8-second server-side open-answer evaluation deadline;
- no session/evidence write when the evaluator deadline or provider fails;
- a synchronous frontend submit latch for same-tick duplicate clicks;
- frontend session reconciliation after an ambiguous client-side timeout;
- atomic persistence of the accepted attempt evidence and curriculum state.

After the fix, Chapter 3 completed through visible controls at 11/11 and opened
Chapter 4. Chapter 4 accepted an original humane opinion instead of requiring
one memorized answer:

```text
He should have unlocked the cage because animals deserve to choose where they live.
```

The browser then reached Chapter 4 Level 9 and submitted a structurally valid,
original 76-word continuation using wording outside the old keyword list. The
local `qwen2.5:14b` evaluator exceeded the deadline. Post-fix behavior was:

```text
browser request duration -> 10,004 ms
HTTP result -> 503 open_answer_evaluation_timeout
visible message -> Review is taking longer than expected. Your answer was not submitted, so please try again.
textarea -> original answer retained
curriculum progress -> remained 8/10
learning event/session mutation -> none
```

The production-like Gemini Flash-Lite browser retry was not sent. The external
model submission was blocked before transmission pending explicit approval to
send the authenticated test learner's synthetic writing to Gemini.

Automated verification after the timeout and persistence changes:

```text
122 backend School Rebuild/shared security tests passed
frontend School Rebuild surface check passed
frontend TypeScript passed
frontend ESLint passed with zero warnings
content validator: 47 chapters, 5,405 items, 940 chapter checks
```

Phase 39 verdict:

- PASS: revised chapter versioning and selective reopening.
- PASS: structural nonsense is rejected without model cost.
- PASS: backend, not the model headline score, owns advancement.
- PASS: slow evaluation no longer advances after the browser gives up.
- PASS: original opinion wording and the Chapter 3 recovery flow.
- FAIL: deterministic curriculum requests measured roughly 4.6-5.0 seconds,
  above the intended sub-2-second target.
- BLOCKED: successful real-model grading remains unverified until the external
  Gemini test submission is explicitly approved or a compliant faster local
  evaluator is provided.
- CURRENT BROWSER STATE: Chapter 3 complete; Chapter 4 paused at 8/10 on the
  retained story-continuation answer.

Post-verdict latency hardening removed the answer route's redundant profile
lookup and post-commit session reread. It also added a row-locked optimistic
state check so two tabs cannot commit conflicting evaluations for the same old
activity. A second visible preflight submission measured:

```text
before round-trip reduction -> approximately 4,600-5,001 ms
after round-trip reduction -> 3,276 ms
result -> correct bridge transition, no model call
```

This improves the deterministic path but does not change the latency verdict:
3,276 ms remains above the intended sub-2-second target.

## Phase 40 - Durable answer retries and authenticated replay

Date: 2026-07-11

This phase added a durable answer-request ledger keyed by curriculum session and
activity. Exact retries now replay the committed public response, conflicting
answers are rejected, and in-flight requests cannot invoke the evaluator twice.
A rotating claim token fences stale workers so an expired worker cannot complete
or fail a newer lease.

Review and verification evidence:

```text
focused curriculum/idempotency/security tests -> 88 passed
full backend hardening suite -> 764 passed
frontend TypeScript -> passed
frontend School Rebuild surface contract -> passed
frontend ESLint -> passed with zero warnings
frontend production build -> passed
spec review -> PASS
transaction/code-quality review -> PASS (Postgres two-connection race test remains minor follow-up)
Supabase migration runner -> applied 17 files and validated runtime schema
```

The authenticated Chrome profile on CDP 9225 resumed the persisted Class 5
Chapter 4 state at 8/10. All interactions below used the rendered option,
textarea, and submit controls; no answer API was called directly.

Visible replay:

```text
Bridge: Continue the parrot's story
selected -> it connects to the escape
result -> Good. Now try the same chapter skill without hints.
next activity -> 60-90 word independent story continuation
```

The learner entered an original 71-word continuation. The local evaluator timed
out on the initial submission and one warm retry. Both attempts preserved the
textarea, did not advance 8/10 progress, and showed:

```text
Review is taking longer than expected. Your answer was not submitted, so please try again.
```

Browser resource timings for this replay:

```text
deterministic bridge answer -> 6,781 ms
first open-answer attempt -> 12,917 ms
warm open-answer retry -> 12,899 ms
```

Phase 40 verdict:

- PASS: the current Supabase schema contains the durable request ledger and
  claim-token fence.
- PASS: timeout retries remain recoverable; the answer is preserved and no false
  progress is shown.
- PASS: learner state remains at the exact activity after reload/retry failure.
- FAIL: the deterministic bridge remains far above the sub-2-second target.
- FAIL: synchronous local open-answer evaluation remains a learner dead-end at
  this checkpoint; two consecutive visible submissions exceeded the deadline.
- BLOCKED: Chapter 4 completion and Chapter 5 browser entry require either an
  explicitly approved Gemini evaluation or a product change that provides a
  truthful asynchronous/pending evaluation path. Auto-passing or weakening the
  rubric is not an acceptable workaround.

## Phase 41 - Unbounded local evaluation and full Chapter 4 completion

Date: 2026-07-11

Gemini is no longer available for this build. Local School QA now treats
`AI_BACKEND=local` as an explicitly unbounded runtime:

- Ollama structured requests use no HTTP deadline;
- the backend evaluator has no local `asyncio` deadline;
- the explicit Next School proxy has no abort timer;
- all School browser requests disable the generic 20-second client timeout when
  `NEXT_PUBLIC_SCHOOL_LOCAL_MODE=1`;
- cloud evaluation retains its backend-owned bounded policy;
- a token-fenced heartbeat keeps long answer claims alive and cancels the model
  immediately if the claim is lost.

The retained Chapter 4 continuation was accepted through the authenticated
browser after the local Qwen JSON-repair prompt was tightened to require every
numeric field on a 0.0-1.0 scale. Level 10 then completed and Chapter 5 opened.
A full reload taking about 50 seconds also completed without a false browser
timeout, proving the local no-deadline policy applies to hydration as well as
answer submission.

## Phase 42 - Chapter 5 live learner run and defects found

All interactions used the visible browser controls in the dedicated School
Chrome profile authenticated as `[SCHOOL_QA_ACCOUNT]`.

The first three natural Level 1 answers were incorrectly routed through bridge
and masterclass support. Persisted evidence showed this was not Qwen: the
deterministic concept grader required contiguous canned phrases and awarded
only the word-count criterion. Natural insertions such as `the moss`,
`as its water habitat`, and `different parts` caused false misses.

The repaired deterministic matcher now:

- accepts exact phrases first;
- permits bounded ordered concept-token variants and a small reviewed alias set;
- does not use the unsafe unordered token-bag fallback;
- preserves authored concept sequence;
- blocks local and post-match contradictions conservatively;
- escalates adversative-plus-negation ambiguity to the strict Qwen rubric
  contract instead of pretending a phrase parser understands the sentence.

The first chapter-check Qwen item then exposed an independent identity defect.
The provider correctly echoed `eng_c5_ch05_assess_11`, while the backend required
the immutable `chapter_check:1:eng_c5_ch05_assess_11` activity identity. The
provider call now always receives `activity_id`; chapter-check semantic fallback
events are also persisted as `semantic_llm_rubric`, not `deterministic`.

## Phase 43 - Completed gold slice and continuity verification

The browser completed:

```text
Chapter 5: The Frog
learning levels -> 7/7 complete
chapter-check items -> 13/13 submitted
Qwen-rubric items in the form -> 2 accepted
chapter result -> passed
final visible state -> All available authored chapters complete
```

Persisted result from the original live run:

```text
assessment attempt -> 1
responses -> 13
aggregate score -> 0.9744
passed -> true
```

That historical result is intentionally not rewritten. It contains one false
item failure for the correct sentence `A frog's webbed feet help it push through
the water while swimming.` The authored possessive variant and regression are
now fixed, so future runs do not create the false `vocab.chapter_word_usage`
weakness.

A later authored-variant correction changed `content_version` but not assessment
meaning. The old implementation reopened the completed chapter after reload.
School content now carries a separate `certification_version`: wording and
accepted-variant fixes preserve completion, while assessment-changing revisions
can still deliberately require recertification. Final authenticated reload:

```text
Chapter 1 -> Complete
Chapter 2 -> Complete
Chapter 3 -> Complete
Chapter 4 -> Complete
Chapter 5 -> Complete
source note -> All available target-class chapters are complete.
```

Final verification for this checkpoint:

```text
backend hardening suite -> 784 passed
frontend School surface contract -> passed
frontend TypeScript -> passed
frontend ESLint -> passed with zero warnings
frontend production build -> passed
backend/frontend git diff checks -> passed
```

Remaining product findings:

- deterministic School answer round trips were usually about 7.5-15 seconds;
- state/curriculum hydration reached roughly 50-60 seconds against the current
  remote Supabase setup;
- local Qwen writing turns remain visibly slow and need a better child-facing
  pending/review state even though they no longer fail on an artificial timeout;
- the current activity UI is still a form-and-level runner, not yet the calm,
  conversational personalized tutor experience defined by the product goal;
- only the current authored class 3-5 slice is live, and Chapter 5 is the first
  deeply reviewed gold slice rather than proof that every class 2-5 chapter has
  equivalent depth.

## Phase 44 - Local Qwen has no application wall-clock deadline

The `8s` open-answer SLA is a hosted-production requirement only. Local School
development now has no hard model-call deadline across structured, streaming,
or complete Ollama request shapes. The School backend evaluator, explicit Next
proxy, and browser client were already unbounded in local mode; this checkpoint
removed the remaining 300-second streaming and 180-second completion limits.

Verification:

```text
local Ollama no-deadline/retry tests -> 6 passed
School local timeout/claim contract selection -> 14 passed
frontend School rebuild surface contract -> passed
```

Cancellation, lost-claim fencing, process failure, and network failure still
terminate work. Elapsed time alone does not fail a valid local Qwen response.
