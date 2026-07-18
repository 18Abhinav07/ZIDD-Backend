---
created: 2026-07-10
last-updated: 2026-07-13
project: zidd
ecosystem: full-stack
tags: [school-prep, architecture, curriculum, pedagogy, personalization]
status: approved
approved: 2026-07-13
approved-by: product-owner
---

# School Prep Canonical Architecture Contract

Backlinks: [[HANDOFF]] [[validation/school-prep-current-product-audit]]

## Status

This is the approved canonical architecture contract for the `/school` product.
It replaces the earlier V1/V2/V3 implementation direction and authorizes phased
runtime implementation under the gates defined in this document.

The current visual redesign, versioned onboarding, generic School sessions,
lineage constraints, linked-session foreign keys, answer idempotency, and atomic
answer persistence are reusable. The content, competency identity, learner
projection, placement depth, recap planner, support flow, and target-class
adaptation are not production-complete and must be replaced behind the canonical
`/school` contract.

## Product Promise

> Tell Zidd your class, subject, school context, and comfortable teaching
> language. Zidd finds the safest starting point, builds only the prerequisite
> work you need, prepares you for your real curriculum, and then adapts teaching,
> checks, support, review, and progression from evidence gathered over time.

The product is not a textbook chatbot, a question bank, or a static chapter
reader. It is an evidence-backed readiness and curriculum-support system.

## Non-Negotiable Invariants

1. The backend owns progression, readiness, mastery, unlocks, branching, support
   caps, review scheduling, and report validity.
2. Every mastery or weakness claim traces to committed learner evidence.
3. Supported practice and independent certification are distinct signals.
4. Class-level difficulty is part of competency identity. Class 2 evidence can
   never certify a Class 5 standard with the same generic skill name.
5. Runtime models cannot invent placement questions, answer keys, rubrics,
   curriculum facts, standards, or certification decisions.
6. Hindi or Hinglish may scaffold instruction. Independent English-subject
   certification still requires the item-defined English evidence.
7. Unavailable modalities produce `not_assessed`, never inferred proficiency.
8. No learner can loop indefinitely in placement, recap, masterclass, support,
   chapter remediation, or assessment.
9. The current `/school` API and UI are canonical. No V4/V5 learner-facing
   namespace is created.
10. Public responses never expose answer keys, accepted answers, hidden rubrics,
    model answers, scoring thresholds, or private planner state.

## Verified Curriculum Release

The initial release is English, Classes 2-5, aligned to the official NCERT
2026-27 reprints:

| Class | Book | Official code/PDF | Repo chapter count |
| --- | --- | --- | ---: |
| 2 | Mridang | [`bemr1`](https://ncert.nic.in/textbook/pdf/bemr1ps.pdf) | 13 mapped lesson modules |
| 3 | Santoor | [`cesa1`](https://ncert.nic.in/textbook/pdf/cesa1ps.pdf) | 12 numbered chapters |
| 4 | Santoor | [`desa1`](https://ncert.nic.in/textbook/pdf/desa1ps.pdf) | 12 numbered chapters |
| 5 | Santoor | [`eesa1`](https://ncert.nic.in/textbook/pdf/eesa1ps.pdf) | 10 numbered chapters |

The release registry must also represent units, picture-reading sections,
self-assessments, and other structural modules. Forty-seven chapter titles alone
are not a complete course map.

Each release record contains:

- `curriculum_release_id`;
- board, subject, class, academic year, book title, book code, ISBN;
- official source URLs and source hashes;
- first-edition and reprint metadata;
- ordered units and structural modules;
- effective and retired dates;
- verification status and evidence.

Changing a release creates a new immutable release. Existing reports retain the
release and certification version under which evidence was produced.

## Copyright And Content Boundary

Official textbooks are authoring references. Product runtime stores original
Zidd teaching content, examples, passages, questions, feedback, and rubrics.
Verbatim textbook bodies are not stored or served unless licensing is resolved.

An offline authoring workspace may inspect official source material. It produces
a private coverage map of facts, themes, sequence, activities, curricular goals,
and grade outcomes. Release validation checks original Zidd content against that
map and checks that it does not copy source prose beyond approved short labels.

## Content Architecture

### Storage

Curriculum content lives as version-controlled, schema-validated authoring files.
A build step compiles approved files into an immutable indexed release package.
The backend loads the package once and caches indexes by release, class, chapter,
competency standard, activity type, misconception, language scaffold, and
difficulty. Audio, images, and larger media use object storage/CDN references
with content hashes. The database stores content IDs and versions, not content
bodies.

### Structural Types

- `CurriculumRelease`
- `CurriculumUnit`
- `CurriculumModule`: chapter, poem, story, picture reading, self-assessment,
  activity, or review
- `ChapterCoverageMap`
- `LearningOutcome`
- `CompetencyStandardRef`
- `TeachingBlock`
- `WorkedExample`
- `ActivityItem`
- `MisconceptionCluster`
- `OpenAnswerRubric`
- `ChapterAssessment`
- `ContentApprovalEvidence`

### Activity Types

The content and frontend renderer support:

- multiple choice and multi-select;
- short exact and fill blank;
- constructed short and extended response;
- ordering and sentence construction;
- matching and classification;
- image observation and hotspot selection;
- listening comprehension;
- read-aloud or oral response when microphone support is available;
- role-play or spoken practice;
- guided exploration, drawing, game, or offline action with a verifiable follow-up;
- reflection that is explicitly non-certifying.

### 8+ Production Content Gate

Every production module must have:

- verified release and coverage-map references;
- 5-7 meaningful outcomes for normal chapters, or a justified module-specific
  count;
- explicit prerequisite standards;
- teaching before performance;
- worked examples;
- at least 4 unique guided and 4 unique independent items per outcome;
- at least 3 unique transfer items per outcome and 2 review items per certifying
  standard;
- at least 5 targeted support checks and 2 distinct reteaching strategies per
  authored misconception cluster;
- at least 20 chapter-assessment items for a normal chapter;
- strict rubrics for every open answer;
- English, Hindi, and Hinglish instruction support where applicable;
- reading-level, factual, answer-key, rubric, similarity, leakage, and duplicate
  validation;
- review evidence that identifies who or what reviewed pedagogy, language,
  correctness, and runtime behavior.

Numeric volume does not satisfy the gate when prompts, passages, answers, or
rubrics are semantically duplicated. The existing generated V3 seed corpus is
never eligible for production approval.

The normal-chapter minimum is intentionally large: roughly 95-120 unique items
depending on outcome and misconception count, before structural modules and
media. The full release is expected to exceed 4,500 substantive items. That is a
content-production programme, not one implementation task.

Authoring scales in release batches: gold slice, complete Class 2, complete
Class 3, complete Class 4, then complete Class 5. A batch is not learner-visible
until every source module in that class passes the gate; internal QA may expose
individual modules behind a non-production flag.

Generic prerequisite items may be referenced by several chapter overlays but
exist once in the global foundation library. They count toward a chapter's
available support pool only when their standard, band, language, and
misconception tags match. The same item cannot occupy two nodes in one learner
plan and cannot count as chapter-specific coverage. Chapter assessment items are
never shared across chapters.

Each chapter receives automated structural/duplicate/leakage/readability checks,
an editorial and pedagogical review record, answer-key self-verification, rubric
challenge examples, and one browser teaching run. Agent review is labeled as
agent review; it is never represented as qualified-teacher approval. A qualified
teacher review remains a launch requirement for school-partnership claims.

Approval statuses are `draft`, `agent_qa_approved`, `product_owner_approved`,
and `qualified_teacher_approved`. The user has explicitly authorized agent-led
review so implementation and controlled family beta may proceed through
`product_owner_approved` without waiting for an external reviewer. This is a
declared product-risk decision, not a claim of expert validation. Public school
partnerships, institutional efficacy claims, and `teacher reviewed` marketing
require `qualified_teacher_approved` for the complete release.

## Banded Competency Graph

### Identity

`skill_id` names a durable capability family. `proficiency_band_id` names the
grade/difficulty standard at which it is demonstrated. A certifiable node is:

```text
subject_id + skill_id + proficiency_band_id + taxonomy_version
```

Example:

```text
reading.sentence_comprehension@foundation
reading.sentence_comprehension@class_2
reading.sentence_comprehension@class_3
reading.sentence_comprehension@class_4
reading.sentence_comprehension@class_5
```

### Domains

- listening and oral comprehension;
- speaking and oral production;
- reading and viewing;
- vocabulary in context;
- grammar and language use;
- written expression;
- curriculum-module knowledge outcomes.

Each standard contains prerequisites, observable descriptors, accepted evidence
modes, certifying language, difficulty anchors, misconception links, and review
policy.

### Prerequisite Closure

The graph is acyclic and topologically validated. A Class 5 summary standard may
depend on Class 4 short-answer writing, Class 3 complete-sentence writing, and
Class 2 sentence comprehension. The path compiler always includes the lowest
unready prerequisite before its dependent standard.

### Instructional Progression

The competency descriptors and content gates enforce an age progression rather
than applying the same generic skill at greater text length:

- Foundation/Class 2: familiar oral language, listening, sound/word recognition,
  vocabulary through visuals and context, sentence meaning, picture talk,
  guided sentence construction, rhyme/play, and short read-aloud work.
- Class 3: fluent short-passage reading, sequence and main idea, explicit-clue
  inference, vocabulary and grammar in context, oral retell, and guided short
  responses moving toward independence.
- Class 4: sustained passage comprehension, evidence-backed reasons, comparison,
  paragraph organization, grammar for meaning, and increasingly independent
  speaking and writing.
- Class 5: multi-paragraph comprehension, inference and synthesis, own-words
  summary, purpose/audience, structured written response, discussion, and
  transfer to unfamiliar contexts.

Every activity declares cognitive load, expected completion time, scaffold
level, and withdrawal rule. Activity passages normally stay within 20-80 words
for Class 2, 50-150 for Class 3, 80-250 for Class 4, and 120-350 for Class 5;
longer authentic chapter work is chunked with continuity preserved. These bands
are validated against the gold slice and may be versioned, not silently changed.

Feedback addresses at most one primary misconception per turn. The first miss
gets a concise clue; a repeated miss gets a worked example or alternate modality;
the learner then returns to a fresh independent item. Scaffold withdrawal is
evidence-based, never calendar-based. A learner may stop at any completed node;
the system does not force an arbitrary fixed-duration session.

## Evidence And Mastery Authority

### Evidence Ledger

Every evaluated learner action produces immutable `SchoolAttemptEvidence`:

- user, profile version, session, flow, subject;
- curriculum release, taxonomy, content, rubric, and certification versions;
- competency standard IDs;
- activity and attempt type;
- evaluator score and confidence;
- support level and hint count;
- language required and detected;
- criteria, evidence excerpts, misconceptions, blockers, and caveats;
- evaluator mode/model/prompt version when applicable;
- event time and idempotency key.

### Projection

`school_skill_profiles` is keyed by user, subject, skill, proficiency band, and
taxonomy version **and certification epoch**. It stores the serialized shared
readiness state plus trend, review schedule, evidence counts, active
misconceptions, and content/rubric compatibility metadata.

Evidence joins an existing projection only when subject, standard, taxonomy
version, certification epoch, language requirement, and assessment-mode policy
are compatible. A copy-only content revision may declare compatibility in a
signed release manifest. A changed rubric, pass rule, standard descriptor, or
certifying modality creates a new certification epoch. The projector replays
only compatible evidence into that epoch; older evidence remains historical and
cannot silently unlock the new standard.

Only one projector may update this state. Placement, recap, masterclass,
curriculum, review, and chapter assessment all call the same projector.

### Transaction Boundary

An answer transaction commits together:

1. answer-request completion;
2. visible session event;
3. immutable learning evidence;
4. updated learner projection;
5. updated session snapshot;
6. report or branch transition when produced.

The next activity cannot be returned from a newer session state while the
learner projection remains stale. A replay worker may repair projections from
the ledger, but normal correctness does not depend on best-effort side effects.

### Readiness Contract

The canonical state contains `practice_readiness`, `certified_readiness`, total
and certifying attempt counts, independent/transfer/review/chapter pass counts,
ready source, active blockers, the last five hint/support flags, and last
confidence.

Attempt score remains the actual evaluator score. Attempt type changes only the
EMA movement rate:

| Attempt | Base alpha | Certifying eligible |
| --- | ---: | --- |
| bridge | 0.15 | no |
| guided | 0.25 | no |
| placement | 0.30 | no; confirmed-ready seed is separate |
| independent check | 0.45 | yes |
| transfer check | 0.50 | yes |
| review check | 0.40 | yes |
| chapter check | 0.55 | yes |

The effective alpha is `base_alpha * evaluator_confidence`. The first eligible
attempt sets the corresponding readiness directly; later attempts use
`previous + effective_alpha * (score - previous)`. Scores and confidence are
clamped to `[0, 1]`.

Update matrix:

- every scorable attempt, including guided, bridge, placement, independent,
  transfer, review, and chapter checks, updates `practice_readiness`;
- only a blocker-free independent `independent_check`, `transfer_check`,
  `review_check`, or `chapter_check` updates `certified_readiness` and certifying
  pass counters;
- a placement attempt updates practice readiness only; the separate
  confirmed-ready seed may set certified readiness to 0.80 after the complete
  placement verdict;
- unscorable, provider-failed, skipped, or invalid-modality attempts update
  neither readiness value, though they remain session/quality events;
- multi-standard items apply the same evaluator score independently only to
  standards explicitly marked `scored_standard_ids`; telemetry tags receive no
  readiness update.

Pass threshold is `0.80`; ready threshold is `0.80`; mastery threshold is
`0.90`. A certifying attempt must be independent, use a certifying attempt type,
match the required language/modality, and have no active attempt blocker.

Status definitions are:

1. `unseen`: no evidence;
2. `weak`: evidence exists but practice readiness is below 0.80;
3. `practice_ready`: practice readiness is at least 0.80 without valid ready
   evidence;
4. `ready`: certified readiness is at least 0.80 and either two independent
   passes exist or a confirmed placement seed set readiness to exactly 0.80;
5. `mastered`: certified readiness is at least 0.90, at least three independent
   passes and one transfer pass exist, no unresolved blockers exist, and fewer
   than 25% of the last five attempts used hints/support;
6. `review_due`: a previously ready/mastered standard reached its due date
   without a passing review. It is not valid for a new unlock until reviewed.

Classification checks `review_due` before returning ready/mastered, then checks
mastered, ready, practice-ready, unseen, and weak in that order.

A confirmed placement-ready verdict may seed certified readiness at `0.80`; it
does not increment independent passes and can never create mastery. Review
intervals are 3 days for ready, 7 days for mastered, double after each passing
review to a 30-day maximum, and collapse to 1 day after failure.

Attempt blockers include language mismatch, copied exemplar, missing required
criterion, invalid modality, excessive support on a certifying task, and explicit
rubric blockers. A blocker remains active until a later independent qualifying
attempt demonstrates the blocked criterion; guided success cannot clear it.
Later independent failure updates the EMA and may regress ready or mastered state
to `review_due` or `weak`.

No SQL `GREATEST` rule may make School mastery permanent.

## Learner Memory

### Hot Session Memory

The current session snapshot contains only information needed for the next turn:

- current objective and plan node;
- recent attempts and feedback;
- active misconception hypothesis;
- support used in this episode;
- pending branch or handoff;
- unused content variants;
- current language scaffold level.

It updates with every committed answer.

### Longitudinal Memory

Session start retrieves a compact projection:

- active prerequisite gaps;
- watchlist standards;
- improving and stable standards;
- current misconceptions;
- hint/language dependencies;
- due reviews;
- recent growth evidence;
- unresolved support episodes.

Historical weaknesses remain in evidence history but leave the active prompt
context after sufficient qualifying evidence.

## Onboarding

The existing versioned onboarding flow is retained. It captures learner name,
school, board, target class, subjects, teaching language, English comfort,
learner/parent goals, and prior difficulty signals.

Usage rules:

- target class and subject choose release and placement scope;
- preferred language controls instruction scaffolding;
- English comfort changes orientation and initial scaffold, not certification;
- prior difficulty signals prioritize placement order but do not pre-score;
- school/board determine supported curriculum or an honest incompatibility state;
- goals change examples and reports, not mastery thresholds.

## Placement Architecture

Placement finds a safe starting path, not a complete psychological profile.

Each target class defines exactly eight diagnostic tracks. A track owns one
primary competency family, an ordered list of authored proficiency bands, and
at least two unused variants per reachable band. Secondary skill tags are
telemetry only and never receive copied readiness evidence.

Placement classification is deterministic:

- `pass`: score >= 0.80, confidence >= 0.75, no blocker;
- `fail`: score < 0.60, confidence >= 0.70;
- `ambiguous`: score from 0.60 to below 0.80, confidence below the required
  threshold, skip, certifying-language mismatch, or conflicting criteria;
- `unscorable`: provider/contract failure or unavailable required modality.

Skipped, ambiguous, and unscorable attempts consume neither a pass nor a fail.
An unscorable provider attempt does not consume the authored item and may be
retried through the evaluation lifecycle.

### Module 1: Broad Snapshot

- eight high-signal tasks covering the major prerequisite clusters;
- short, understandable, self-contained context;
- preferred-language instructions without translating the English evidence being
  assessed;
- target and near-target anchors;
- at most three LLM-graded open responses;
- exits on complete coverage, 8 items, or 240 seconds of learner time.

### Module 2: Targeted Diagnostic

- selects only failed, ambiguous, skipped, mismatched, or contradictory clusters;
- searches all lower proficiency bands available below the target class;
- uses binary or bounded downward search rather than replaying every class;
- preserves per-standard confidence and does not copy one result across skills;
- exits after 300 seconds of learner time or when the total placement budget
  requires reserving confirmation capacity.

Every unresolved track maintains `highest_passed_band` and
`lowest_failed_band`. The selector chooses the midpoint untested authored band
between them. With no passed lower bound, it moves downward toward the lowest
available prerequisite anchor; with no failed upper bound, it moves upward.
Tracks are scheduled by blocking prerequisite first, then ambiguity, prior
difficulty signal, and stable track order. One track cannot consume more than
three targeted/confirmatory items while another blocking track has no targeted
evidence.

### Module 3: Confirmation

- runs only for contradictory or low-confidence blocking standards;
- uses unused authored variants;
- may be resumed later without restarting completed modules;
- uses at most 4 items or 180 seconds of learner time.

Confirmation is required when a **weak or downward boundary** depends on one
attempt, a higher band passed while a lower band failed, criteria disagree, or
the selected overall starting band would change based on that track. A clean
Stage-1 target-anchor pass with score/confidence >= 0.85, no blockers, and no
contradictory onboarding or historical signal may resolve placement readiness
without a second item because placement seeds access, not mastery. It uses a
different context and item variant from every earlier attempt.

### Bounds And Honesty

The initial outer budget is 18 items. Stage 1 uses at most 8. Stage 2 may use up
to 10 only when confirmation is unnecessary; otherwise it hands off by item 14
so Stage 3 retains four items. If the budget cannot resolve every standard,
placement returns a safe starting band plus `unknown` or
`insufficient_evidence` standards. Early Readiness Path nodes continue
diagnosis. It does not claim to know every skill from 18 questions.

The four reserved confirmation items are prioritized to standards that can
change unlock or the overall starting band. `below_target` needs one confirmed
blocking gap, not confirmation of every provisional weakness. Additional
unconfirmed weak signals become early-diagnostic nodes and cannot be reported as
certified gaps. If more than four unlock-critical tracks require confirmation,
the result is `insufficient_evidence`, not a fabricated boundary.

Server timestamps enforce stage and overall wall-clock limits. Model-evaluation
time is recorded separately and does not consume the learner's thinking budget.

A track is `resolved_ready` when its target anchor passes with required
confidence and has no contradictory lower evidence. A track is
`confirmed_weak` when a target/prerequisite anchor fails and an independent
second item confirms the same boundary or a lower-band pass establishes the
highest safe band. Otherwise it remains unresolved.

`target_ready` requires all blocking tracks resolved ready. Non-blocking
ambiguity becomes a watchlist only when no prerequisite unlock depends on it.
`below_target` requires at least one confirmed blocking gap with confidence >=
0.75. `insufficient_evidence` is used when neither conclusion is defensible.

The parent-facing `evaluated_class_no` is emitted only when at least three of the
four class-anchor tracks have confirmed highest-safe bands within one class of
each other. It is the minimum of those confirmed bands. Otherwise the report
shows per-track starting bands without inventing one overall class label.

### Output

- placement status and confidence;
- per-standard status and evidence;
- safe starting band, when defensible;
- blocking prerequisite standards;
- early-diagnostic standards;
- target-class watchlist;
- allowed next actions;
- learner and parent explanations;
- immutable source profile/release/taxonomy versions.

`insufficient_evidence` is resumable while unused diagnostic work exists. A truly
terminal insufficient session authorizes a new continuation session linked to
the previous evidence; it never exposes a dead Continue button.

At most one automatic continuation session is allowed per profile version and
placement release. If that continuation also ends insufficient, placement moves
to `diagnostic_incomplete`, target access remains locked, and the parent report
offers profile correction, retry after a new placement release, or external
support. The backend does not auto-create a third placement session.

## Adaptive Journey Compiler

The compiler accepts profile, placement report, current learner projection,
target standards, prerequisite graph, approved content indexes, and policy
limits. It produces an immutable `SchoolJourneyPlan` with versioned nodes and
edges.

Every plan has `plan_id`, monotonically increasing `plan_version`, `status`,
`supersedes_plan_version`, source evidence watermark, profile/release/taxonomy/
certification versions, active node, reserved content IDs, and creation reason.
There is one active plan version per user, profile lineage, subject, and flow.

Runtime does not mutate a plan. Normal answers move the session cursor through
its active plan. A support cap, newly confirmed prerequisite, incompatible
content revision, or explicit path-revision decision compiles a new version via
compare-and-set at a completed node boundary. The old version becomes
`superseded`; evidence keeps its original plan version and node ID. In-flight
answers against the old version complete or conflict before supersession, never
attach to the new plan accidentally.

Content reservations are scoped to the plan version and learner. Completion
marks them consumed. Supersession or abandonment releases unused reservations
while preserving already served IDs in the learner's exposure history, so a
recompiled plan cannot immediately repeat them.

The deterministic compiler is authoritative and must operate without an LLM.
An optional model may propose ordering among equivalent approved variants or
naturalize learner-facing explanations. Validators reject unknown standards,
content, edges, assessments, or gates.

Plan validators require:

- complete prerequisite closure;
- no cycles or unreachable nodes;
- teaching before certifying checks;
- unused valid variants;
- independent and transfer evidence for unlock-critical standards;
- bounded support and revision paths;
- correct language and modality policy;
- no hidden-field leakage.

## Canonical Teaching Loop

```text
load plan node + hot memory + compact learner projection
-> deterministic teaching policy selects action
-> content resolver selects an unused approved variant
-> tutor renderer presents content and allowed scaffolding
-> evaluator produces structured attempt evidence
-> atomic transaction commits evidence, projection, event, and state
-> policy advances, bridges, branches, reviews, or revises the path
```

Personalization changes starting band, content variant, difficulty, modality,
scaffold language, hint depth, pacing, branch choice, review timing, and
curriculum overlays. Personalized copy alone is not personalization.

## Readiness Path

Below-target learners receive only missing prerequisite closure, not a replay of
entire lower classes.

Each path node contains teaching, worked example, guided activity, optional
bridge, independent check, transfer check, and failure policy. Low-confidence
placement standards start with a microdiagnostic node before teaching.

Qualifying evidence updates the same longitudinal projection used by curriculum.
Unlock occurs only when every blocking prerequisite standard is ready. Residual
non-blocking standards become a visible watchlist with a deviation note.

Repeated struggle changes modality, example family, or prerequisite depth. It
does not repeat the same prompt under a new label.

## Support And Masterclass

A `SupportEpisode` is a linked session with:

- trigger evidence and misconception;
- source plan/session/node;
- teaching strategy and modality;
- reserved variant IDs;
- independent return check;
- attempt and branch budget;
- completion, abandonment, cap, and revision outcome.

Target curriculum allows at most two automatic masterclass interruptions for
the same weak-skill episode. Abandonment consumes the cap. The third trigger
creates an executable support-plan state, never another masterclass and never a
dead report page.

Readiness Path support uses a bounded node support budget. Exhaustion recompiles
the path at a lower prerequisite or alternate modality. It does not apply the
target-class interruption cap mechanically, but it also cannot loop.

Each standard episode allows at most two support branches and two plan
revisions. A revision must strictly decrease prerequisite depth, select a
previously unused pedagogy/modality, or remove an invalid modality; a validator
rejects a revision with no measurable change. A Readiness Path allows at most
three superseding plan versions overall. Exhaustion produces
`needs_external_support`, preserves all evidence, keeps target access locked only
for genuinely blocking standards, and exposes a parent-facing next action. It
never silently compiles a fourth plan.

## Target Curriculum Adaptation

Every chapter has an immutable base outcome graph. At chapter start, the
compiler overlays learner-specific nodes:

- prerequisite reminders before dependent outcomes;
- watchlist probes at relevant points;
- extra guided variants for recently unstable standards;
- due review checks;
- language scaffolding chosen from the language confidence signal;
- branch policies for known misconceptions.

Target-ready learners receive the base graph plus normal review. Learners coming
through Readiness Path receive a modified graph. Both still study the real
target chapter; personalization does not replace curriculum coverage.

Chapter completion requires required outcomes and a valid chapter assessment.
A chapter without a launch-gate assessment cannot become complete.

## Evaluation

1. deterministic grading for objective formats;
2. normalization and accepted alternatives;
3. deterministic structural preflight for open answers;
4. strict-schema model evaluation where semantic judgment is necessary;
5. backend criterion recomputation and blocker policy;
6. evidence projection through the shared readiness engine.

Invalid provider output, provider failure, or uncertain evidence returns a
recoverable pending/unscorable state. It does not become a wrong answer.

Local Qwen has no hard evaluation timeout and renews its answer claim. Production
uses a provider-neutral evaluator interface; Gemini is not a required School
dependency. An evaluation that cannot complete inside the interactive response
window remains a persisted `evaluation_pending` claim processed by a worker.
`GET /school/state` and the active-session endpoint expose Reviewing status and
poll/reload recovery without allowing a second answer. Local Qwen may continue
for 50-60 seconds or longer without turning the attempt into failure.

Evaluation lifecycle:

1. preflight and answer claim commit within 1 second;
2. deterministic evaluation completes inline;
3. semantic evaluation returns `202 evaluation_pending` after 8 seconds in
   hosted mode and immediately after durable job creation in local-worker mode;
4. the worker renews a 120-second lease every 30 seconds;
5. a missing heartbeat makes the job reclaimable without consuming the item;
6. at 180 seconds the UI offers Leave and continue later while the worker may
   continue; this does not cancel or penalize the answer;
7. a provider contract failure receives one repair/retry with the same immutable
   answer and rubric;
8. after two provider failures or 10 minutes without a valid result, the attempt
   becomes `unscorable_provider_failure`, records no readiness movement, releases
   the session to an unused equivalent item or a safe defer state, and surfaces
   telemetry for investigation.

Thus the local model has no short compute timeout, but a learner is never trapped
behind an indefinitely renewing job. Late valid results for a terminally
unscorable claim are discarded by claim token/version checks.

## Language Support

`preferred_teaching_language` is `en`, `hi`, or `hi_en`. Teaching explanations,
orientation, glossary help, and hints follow that preference. English curriculum
passages and certification requirements remain item-defined.

`lang.en_production_confidence` is a non-certifying meta-signal based only on
real language evidence, hints, glossary use, and mismatches. It controls how
quickly English-first prompts appear. It never enters readiness or mastery math.

## API And State Authority

The canonical API remains under `/school`. `GET /school/state` remains the only
frontend next-action authority. It resolves onboarding, placement, report,
Readiness Path, curriculum, masterclass, support, review, and reports from current
profile lineage.

Required new backend capabilities are implemented behind canonical routes:

- learner projection and evidence retrieval;
- resumable placement continuation;
- compiled Readiness Path retrieval/versioning;
- path revision;
- support-plan creation, execution, and completion;
- learner-specific chapter plan retrieval;
- due review execution;
- live learner and parent reports.

Legacy `/subjects` routes remain redirects. Unmounted V1/V2/V3 handlers,
services, seed content, and active imports are archived after current-lineage
migration and compatibility evidence.

## UI Contract

The approved visual-aid direction and Career Prep visual grammar remain the
foundation:

- Instrument Serif display hierarchy and Geist functional text;
- one primary action per screen;
- calm editorial density;
- class map -> chapter map -> level map -> teaching workspace;
- backend-truth-driven states and skeleton loading;
- parent detail behind progressive disclosure;
- no raw standards or engineering status.

Coach avatars are selected once per profile/journey/session and persisted. The
avatar's palette defines accents for that surface. Random selection cannot change
on rerender, reload, or device.

The current learning shell is extended with multimodal activity renderers rather
than replaced with another design system.

## Cost And Latency

Runtime model calls are limited to semantic open-answer evaluation and optional
short naturalization. Placement and plan compilation are deterministic. Objective
items, routing, mastery, reports, and authored feedback require no model.

Track per flow:

- model calls and tokens;
- evaluation latency;
- fallback and invalid-output rate;
- cost per active learner and completed chapter;
- percentage of turns served without a model.

The revenue model must be tested against observed calls per placement, Readiness
Path module, and chapter. No plan assumes free or permanently available Gemini.

Initial operating budgets:

- placement: at most 3 semantic-evaluator calls;
- Readiness Path module: at most 2 semantic-evaluator calls before path revision;
- normal chapter: at most 8 semantic-evaluator calls including chapter checks;
- evaluator prompt: at most 2,500 input tokens and 700 output tokens;
- deterministic API response: p95 below 2 seconds, with evaluator-independent
  policy work below 500 ms;
- pending acknowledgement: p95 below 1 second after the async cutover;
- local Qwen final evaluation: monitored target p95 below 90 seconds, without a
  short failure timeout;
- hosted evaluator: target p95 below 8 seconds, otherwise use pending state;
- monthly model COGS target below 15% of net School subscription revenue and a
  circuit-breaker review at 25%.

These are launch budgets, not mastery inputs. Exceeding them changes provider,
item mix, caching, or pricing; it cannot silently remove required open-answer
evidence.

## Entitlement And Child-Data Boundary

The free product includes onboarding, placement, the complete readiness report,
and one clearly bounded demonstration lesson. Readiness Path execution, ongoing
curriculum tutoring, masterclasses, longitudinal reports, and scheduled reviews
require a family subscription or school-sponsored entitlement. The backend owns
entitlements; the frontend cannot unlock a paid learning session from local
state.

Placement and the report remain free because they are the trust and conversion
surface. The demonstration is one lesson total per learner for the initial
English release, not one per class or subject.

Child data is minimized and purpose-bound:

- raw answers are stored only where needed for evidence, feedback, dispute, and
  learning continuity;
- analytics receives derived event types, not unrestricted child transcripts;
- parent/guardian access and deletion/export paths are explicit before school or
  under-13 launch;
- model prompts contain only the current task, approved content, and compact
  learner context required for that turn;
- provider logs and retention are disabled or contractually bounded for
  production child data;
- share links use scoped, expiring tokens and never expose hidden evidence.

## Persistence Changes

Retain:

- `school_profile_versions`;
- `school_sessions`;
- `school_answer_requests`;
- `school_placement_reports`;
- linked-session and one-active-flow constraints.

Add or strengthen:

- typed version columns on learning evidence;
- `school_session_events` for visible/decision transitions;
- banded `school_skill_profiles`;
- immutable plan/version fields in School session snapshots;
- curriculum release/version references;
- transactional projection updates;
- replay/rebuild utilities and consistency checks.

Do not use generic career `learner_skill_profiles` as the authoritative School
projection. Legacy `school_skill_mastery` and `school_results` become migration
inputs only.

## Implementation Phases And Gates

### Phase 0: Authority And Release Lock

- freeze the 2026-27 release manifest including structural modules;
- identify canonical and archived source/runtime modules;
- lock API/state and migration compatibility.

Gate: source-map verifier, release hashes, route authority audit, no conflicting
mounted School router.

### Phase 1: Banded Standards And Evidence Authority

- introduce banded standards;
- add School evidence/session-event/projection persistence;
- route all attempt types through one projector;
- remove alternate School readiness formulas and monotonic mastery.

Gate: event replay reproduces projection; Class 2/Class 5 evidence does not
collide; later failure can regress mastery; answer and projection commit together.

### Phase 2: Gold Journey Slice

- fully author one target chapter and its prerequisite closure;
- build compiler, teaching policy, multimodal renderer, evaluator, support, and
  target overlay on this slice.

Gate: real browser learners complete target-ready and below-target journeys;
weak answers branch correctly; no false advancement; reload works at every state.

### Phase 3: Multi-Band Placement

- author all lower-band diagnostic anchors and variants for Classes 2-5;
- implement staged selection, timing, continuation, and reports.

Gate: browser traces prove Class 5->5, Class 5->4, Class 5->3, Class 5->2,
contradictory, insufficient, bilingual, abandoned, duplicate, and no-key-leak
flows.

### Phase 4: Readiness Path And Support

- compile focused paths from missing prerequisites;
- add microdiagnostics, path revision, linked support, and cap handling.

Gate: different evidence creates different validated plans; repeated failure
changes strategy and terminates safely; qualifying recap evidence updates the
same learner projection and unlocks only the correct target.

### Phase 5: Target Curriculum Adaptation

- overlay watchlist, reinforcement, review, and misconception policies on target
  chapters;
- make reports read live projections.

Gate: target-ready and recap learners receive observably different valid plans;
resolved weaknesses leave active context; parent reports show evidence-backed
growth.

### Phase 6: Complete Content Release

- bring every verified Class 2-5 module through the gold content gate;
- include picture reading, self-assessment, listening/speaking, and interactive
  activities;
- remove generated seed and incomplete launch content from serving paths.

Gate: complete release coverage, zero content-audit failures, no duplicated seed
patterns, every assessment self-grades or validates correctly, production loader
serves the intended catalog.

### Phase 7: Product QA And Legacy Retirement

- run full authenticated browser journeys with dedicated School profile;
- run mobile/tablet/desktop UI and accessibility QA;
- audit database evidence, reports, latency, cost, and recovery;
- archive old School runtime after migration criteria pass.

Gate: zero P0 issues for 14 days, at least 90% of active School learners on the
canonical lineage, legacy APIs read-only for one release window, then removed.

## Per-Phase Verification Protocol

Every phase uses:

1. focused contract tests for the changed invariant;
2. real PostgreSQL/Supabase integration where persistence changed;
3. authenticated browser QA through the dedicated School Chrome profile;
4. database evidence showing the expected committed state;
5. one subagent implementation review;
6. one adversarial product/pedagogy review;
7. fixes and targeted rerun before proceeding.

Large passing-test totals are regression evidence, not product proof. Browser
behavior and committed learner evidence are the primary acceptance evidence.

Browser acceptance matrix:

- dedicated School Chrome profile authenticated as the School QA user;
- viewports `390x844`, `768x1024`, and `1440x900`;
- current Chrome normal network plus Fast 3G for loading/recovery checks;
- microphone granted, denied, interrupted, and unavailable;
- keyboard-only navigation, visible focus, screen-reader names/status regions,
  and WCAG 2.2 AA contrast/interaction expectations;
- zero unexpected console errors, horizontal overflow, incoherent overlap,
  hidden primary actions, client-only progress, or answer-key leakage;
- screenshot comparison against the approved visual aid for every canonical
  School surface;
- after each critical browser action, deterministic database assertions for
  session state, event IDs, answer claim, projection version, plan version, and
  report lineage.

Gold-slice browser completion requires at least these controlled journeys:
target-ready, below-target, repeated weak/support, bilingual, microphone-denied,
provider-delayed, reload during evaluation, abandon/resume, duplicate submit,
and unauthorized access. Multi-band placement additionally requires two clean
traces for each Class 5->5/4/3/2 conclusion before scale-up.

Initial supported browser policy:

- Chrome and Edge current plus previous major version on desktop;
- Android Chrome current plus previous major version on at least one real phone
  and one real tablet-class device;
- iOS/iPadOS Safari current plus previous major version on real hardware for
  touch, audio, microphone, keyboard, and safe-area behavior;
- macOS Safari current for learner and parent reports;
- Firefox receives best-effort compatibility but is not a launch-blocking
  supported browser for the first release.

Emulated viewports are required on every phase. Real-device Android and iOS
media/input runs are required at the gold-slice, complete-content, and final
launch gates. Unsupported browsers receive an honest compatibility message
rather than a broken learning activity.

## Completion Definition

The product is complete for this scope only when:

- the verified 2026-27 Class 2-5 English structure is production-served;
- onboarding persists and affects allowed personalization dimensions;
- placement can safely find lower starting bands across the supported range;
- below-target learners receive and complete focused Readiness Paths;
- target curriculum is adapted without omitting required coverage;
- support/masterclass/path revision cannot deadlock or loop;
- placement, recap, support, curriculum, assessment, and review update one
  evidence-backed learner projection;
- readiness and mastery cannot be inflated by support or made permanently
  monotonic;
- Hindi/Hinglish scaffolding works without contaminating English certification;
- parent and learner reports use current committed evidence;
- the complete authenticated browser flows pass across supported classes,
  languages, weak/strong learners, reload, abandonment, duplicate submissions,
  and provider failure;
- old School runtime and template content are no longer active authorities.

## Approval Record

The product owner approved this hybrid replacement architecture on 2026-07-13.
Approval authorizes empirical persistence/path spikes, the task-level execution
plan, and phase-by-phase code changes. It does not authorize lowering the content
or browser-QA gates to accelerate completion.
