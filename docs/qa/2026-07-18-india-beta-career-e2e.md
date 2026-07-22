# India Beta Career E2E QA - 2026-07-18

## Scope

Live-browser QA only. No product-code fixes are made during this run.

Target journey:

1. Reset the India beta learner runtime after School QA.
2. Fresh Career onboarding.
3. Exercise a prep journey and a test journey, including completion/report/reload behavior where available.
4. Capture functional, visual, UX, and assessment-quality findings.

## Environment Baseline

- Backend worktree: `mvp-beta-server` at `6aff047`.
- Frontend worktree: `mvp-beta-ui` at `da7586c`.
- Frontend: `http://localhost:3000`.
- Backend: `http://localhost:8000`.
- Browser: dedicated QA Chrome profile through CDP `9222`.
- Data region: India beta. Application learner runtime was reset after School QA; auth, curriculum releases, and migration metadata were preserved.
- Provider health before the combined QA run: Gemini ready and storage writable.

## Evidence Log

| Step | Browser action and observed outcome | Network / state evidence | Findings |
| --- | --- | --- | --- |
| 0 | Reset India beta application learner data after completing School QA. | Reset removed School sessions/evidence, learner profiles, learning events, credits, Career runtime rows, and reports; `auth`, curriculum releases, and migration markers remained untouched. | Clean Career start achieved without resetting another person's history. |
| 1 | Fresh Google sign-in returned through onboarding. Created a Career profile for a Backend Software Engineer with interview goals and a GD topic. | Onboarding state patches and complete request returned `200`. The first navigation to `/career` rendered a shell with empty `main`; reload rendered the dashboard. | **C-001, important navigation reliability:** fresh post-onboarding Career dashboard can be blank until a browser reload. |
| 2 | Chose Interview -> Preparation Mode -> `Tell Me About Yourself`. Submitted a strong pitch, reloaded, then submitted a second pitch focused on a different technical achievement. | Tutor asked for role/current strength/direction; transcript and metrics persisted across reload. First feedback accepted role/proof/direction; second feedback correctly asked for a missing future direction. | **Pass:** career context carried into teaching, feedback was specific to the answer, and session reload continuity worked. The first strong pitch displayed 90% readiness after one attempt, then 65% after a less complete second answer; this is defensible only if the upcoming evidence report makes the aggregation legible. |
| 3 | Switched to Interview Test, configured `Backend Software Engineer`, Technical/Projects, High pressure. Answered two role-specific prompts, then ended early. | Simulator maintained the selected role/type and asked a follow-up about consistency/availability. End confirmation showed `2 / 6` score-eligible and `2 covered / 4 needed`. | **Pass:** test configuration and probe continuity were grounded in the learner profile. |
| 4 | Ended the two-answer test through the visible `End Anyway` path, then reloaded the simulator route. | Final report showed `INSUFFICIENT EVIDENCE`, `Not scored`, concrete evidence caveats, evidence quotes, answered/covered/needed counts, and a next action. The same persisted report reopened after reload. | **Pass:** insufficient simulation evidence did not receive a fabricated numerical score, and the final report persisted across reload. |

## Findings

- **C-001 - Fresh Career dashboard can render blank:** immediately after Career onboarding, `/career` showed only the shared header and an empty main region. A hard reload restored the expected dashboard. This blocks a clean first-use claim until reproducibility is resolved.
- **C-002 - Metric explanation needs product validation:** the tutor changed the readiness display from 90% after the first pitch to 65% after the second, while `Clean passes` remained 0. The feedback itself was appropriate, but a learner cannot infer why the percentage moved. Review the readiness evidence UI before calling Career metrics self-explanatory.
- **C-003 - Model-bound response time remains noticeable:** preparation and assessment turns took roughly 50--120 seconds in this live run. This does not invalidate the assessment contract, but it weakens a real-time coaching experience and needs an explicit pending/return-later product policy.

## Completion Criteria

This report is complete only after a fresh Career learner completes a prep flow and an assessment flow in the live browser, with reports and persistence checked.
