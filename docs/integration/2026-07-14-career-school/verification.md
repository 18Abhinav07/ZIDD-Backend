# Verification Record

## Frozen Inputs

- Career parent: `25a5d4bc878e42455587231bf8c04058cde670d0`
- School parent: `e0e63b3b6750e96842dfc7b6147d939b501a6e0e`
- Core integration tree: `f873c41417f2bd962391354b3b8865ad436c1f53`
- Unresolved merge paths: zero

## Backend Gates

- Focused Career and integration contract gate: 43 passed.
- Production School closure: unavailable by design; 47 chapters are required,
  42 are authored, and 0 are human-approved.
- Disabled production authority mounts only `/school/state` plus explicit
  retirement responses. Career startup remains available.
- School insufficient-evidence state now emits `resume_placement`, matching
  the placement report and the only backend start action that can legally
  continue the learner.
- The additive migration and predecessor handling were exercised against a
  disposable PostgreSQL database during integration. Historical destructive
  School migrations are retained as immutable history, not replayed against a
  Career predecessor.
- The ownership resolver reproduced the exact core tree from the two frozen
  parents.

## Frozen Career Test Parity

A broader assessment selection completed with 134 passed and 11 failed. The
same 11 test nodes fail with the same outputs on a detached worktree at the
frozen Career parent `25a5d4bc878e42455587231bf8c04058cde670d0`.
They are therefore inherited baseline contract mismatches, not integration
regressions. The mismatches concern exact deterministic fallback wording,
repair metadata, one-question GD classification, binding moderator handoffs,
evidence-source labels, and one report-recommendation phrase. The accepted
browser matrix remains the product-quality gate, and no failing behavior was
observed there.

## Inherited School Debt

The frozen School parent contains a stale claim-fencing test fixture that asks
the current Wise Parrot chapter for `wise_parrot_opinion_reason`. The authored
chapter renamed that level to `wise_parrot_freedom_reason`; the fixture fails
with `StopIteration` before claim fencing is exercised. The test, curriculum
loader, and authored JSON involved are byte-identical to the frozen School
parent, so this is recorded source debt rather than an integration regression.

School remains production-disabled until exact 47-chapter closure, human review
evidence, and release attestation all pass.
