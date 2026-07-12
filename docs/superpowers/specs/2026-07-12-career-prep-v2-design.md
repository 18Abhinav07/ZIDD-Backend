# Career Prep V2 Design

## Objective

Raise Interview Prep, GD Prep, Interview Test, and GD Test from the verified 8+ baseline to a 9+ learner experience without rewriting the current engine or weakening assessment integrity.

## Product Contract

1. A learner is never marked ready, resolved, or mastered without distinct, validated evidence for the exact assigned task.
2. Tutor feedback uses the learner's evidence and current role/topic. It never invents employers, achievements, statistics, or personal history.
3. Prep evidence becomes durable, stable skill memory and deliberately influences the next relevant prep or test session.
4. Invalid simulator output remains auditable but cannot improve learner mastery or contaminate future prompts.
5. Every visible action has one clear end-to-end behavior: continue, resume, review, reattempt, practice a named gap, or open a report.

## Evidence Architecture

- Extend prep evaluation context with a stable prompt ID, context ID, active role/topic, assigned participant claims, and semantic anchors.
- Replace prose-hash test gaps with a closed Career skill taxonomy. Prose remains display copy only.
- Classify GD support as learner-owned experience, sourced external evidence, analogy, or explicit hypothetical reasoning. Unsourced numerical claims cannot satisfy evidence criteria.
- Fail closed when GD participant identity or claim polarity is not present in structured prompt context.
- Count readiness and mastery from unique validated evidence records, not repeated mutable counters.
- Derive test report validity from scorable turns, excluded turns, coverage, and repair debt. A fully repaired or excluded run cannot be final.

## Tutor Architecture

- Build deterministic follow-ups from structured role-family and topic slots, with a neutral fallback for unknown roles.
- Keep hypothetical scenarios explicitly labelled and separate from learner-owned history.
- Pass the active GD turn topic into every follow-up and bridge renderer; profile topics are defaults only before a turn begins.
- Select bridge exercises by failed criterion first, then difficulty. A scaffold sequence must return to open production before qualification.
- Anchor feedback to validated criterion evidence quotes. Do not prepend arbitrary learner text merely to simulate personalization.
- Use one canonical criterion contract for content, evaluation, tutor labels, bridges, and advancement.

## Learning Memory

- Merge profile and progression evidence by stable skill ID; authoritative progression mastery cannot be shadowed by a lower profile projection.
- Model `active_gap`, `improving`, `resolved`, and `mastered` as explicit evidence transitions with provenance.
- Keep cumulative attempts and trend evidence across reports. A paraphrase of the same gap must update the same skill.
- Scope memory to the current Interview/GD sibling and exclude invalid or insufficient reports from prompts.
- Add a GD assessment focus plan so previous GD Prep gaps enter the test coverage ledger.
- Make hot-session updates idempotent by evaluation ID.

## Continuity UX

- Add recent prep sessions and test reports to Profile, including timestamp, status, score/readiness, evidence, and next action.
- Reopen persisted test reports through the existing report endpoint.
- Deep-link Practice This Gap and report recovery actions to the exact prep node.
- Use Continue Path unless a real resumable session ID exists. Remove duplicate Save for Later and Leave behavior.
- Use the shared billing balance everywhere and render only backend-owned pricing/entitlement copy.
- Display Checkpoint Passed, Needs Practice, and Mastered as distinct map states with readiness and remaining proof.
- Add editable Career profile fields and an assessment-context preview.
- Apply the existing report-modal focus pattern to all dialogs; fix mobile header density, accessible names, selected-state semantics, and contrast.

## Verification Strategy

- Add only compact contract tests for pure integrity rules and persistence transitions. Do not create another large test file.
- Use authenticated browser runs as the product acceptance source of truth.
- Run representative early/mid/late Interview and GD Prep modules, then one complete Interview Test and one complete GD Test.
- Verify report history, targeted practice, reload/resume, next-session memory carry-over, and desktop/mobile layout.
- Batch fixes before browser reruns; do not rerun all four flows after every small edit.

## Non-Goals

- No voice mode.
- No company-intelligence research system.
- No replacement of the structured assessment engine.
- No pricing-rule change beyond accurate copy and one balance source.
- No School Prep changes.
