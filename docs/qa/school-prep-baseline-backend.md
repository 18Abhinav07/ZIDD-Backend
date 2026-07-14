---
created: 2026-07-13
project: zidd
ecosystem: full-stack
tags: [school-prep, baseline, recovery, backend]
---

# School Prep Backend Baseline

Backlinks: [[docs/superpowers/plans/2026-07-13-school-prep-canonical-rebuild]] [[docs/school-prep-rebuild-architecture-contract]]

## Repository State

- Branch: `school-prep`
- HEAD: `ee7a4b3ddf1a4733a112fc3f38c7cb2b3f542a0f`
- Captured before canonical runtime implementation began.
- Live worktree was not reset, cleaned, or checked out.

## Recovery Artifacts

Directory: `/tmp/zidd-school-baseline-ee7a4b3-186ceba`

| Artifact | SHA-256 |
| --- | --- |
| `backend-tracked.patch` | `f5827e800d07f5f21544c52fd3f7ffaaa716fc7a32592381eab0b45bd9086d23` |
| `backend-status.txt` | `856bc750f00d3cb88faf63b6e9d0cfd7fb61b97cadaab10891c600906971c986` |
| `backend-untracked.tar` | `000081d7217da89ee3e4ddd9a9eb4bd1124f04c986a03afc4ea8d8ecde4a1c17` |

Restore verification:

- `git apply --check` passed against a clean archive of HEAD.
- The untracked archive contains 202 entries.
- The tracked patch and untracked archive were restored into a clean HEAD archive.
- Runtime School file hashes matched the live capture exactly; manifest SHA-256: `0dc4195efd0602d490a405260bc60e63643ddd64077358d0e749a73fab67f099`.

## Ownership Classification

School-owned:

- `app/api/school_rebuild_routes.py`, `app/api/school_routes.py` School hunks;
- `app/content/ncert_source_map/**`, `school_rebuild_*`, `school_v2_*`, `school_v3_*`;
- School migrations dated 2026-07-09 through 2026-07-12;
- `app/services/school_core/**`, `school_rebuild_*`, `school_v2_*`, `school_v3_*`;
- School docs, School scripts, `test_school_*`, and School integration tests.

Shared, hunk review required:

- `app/main.py`, `app/api/me_routes.py`, `app/api/onboarding_routes.py`;
- `app/db/repo.py`, `app/db/schema.sql`, `app/db/schema_guard.py`;
- `app/storage/pg_store.py`, `scripts/apply_migrations.py`, `tests/conftest.py`;
- `app/config.py`, `app/middleware/auth.py`, `app/models.py`, `pytest.ini`.

Career/unrelated, do not stage for School tasks:

- AI/career/simulation/rubric/tutor files without a School-owned hunk;
- interview/GD content and Career contract tests;
- assessment engine files created for Career test hardening.

No baseline commit is created until School-owned staging can be reviewed without capturing unrelated shared-file hunks.

## Legacy School Migration Provenance

Task 0.0 captured these untracked migration bytes before Task 0.5 began in
`backend-current-school.sha256` and independently reproduced them in
`backend-restored-school.sha256`. A 2026-07-13 comparison against the live
worktree produced the same hashes:

| Migration | Pre-Task-0.5 SHA-256 |
| --- | --- |
| `2026-07-09-school-v2-placement.sql` | `e536ccd5adef032a3dc0f76d4056d57c96f278d6132e519e10bcbb921d5f721e` |
| `2026-07-09-school-v2-practice.sql` | `d6f431b3de13721fe0b520230a81236af04da6d529aec274143d68e460ce38cd` |
| `2026-07-09-school-v2-curriculum.sql` | `12715900c832802ee1d729cc1eb733c8ce4e846da63ad91555ae221f5d03ca30` |
| `2026-07-09-school-v3-core.sql` | `d29fb8e40df681b830a0e8f36db9230ac9a97c946fdd2281e90b755da5dfd381` |
| `2026-07-10-school-rebuild-profile.sql` | `4541df5f0a0e11ebc4f3e48dc13620fa4ba8319033a44cd3168832fa1b0cc7fe` |
| `2026-07-10-school-placement-reports.sql` | `68cbad3ee1fcc29700a69c2be423fc184c3647335bed6f60f2636854d1732254` |
| `2026-07-11-school-answer-idempotency.sql` | `d195958bbb3400c77a5255a837d95f9943382549863c04cac26dd7f77a02973b` |
| `2026-07-12-school-session-lineage.sql` | `6998e23b00c8c1d5d4866063a15e98be1a2be8308debf01cc0e07277c719ec15` |
| `2026-07-12-school-onboarding-drafts.sql` | `2d57b79d672ceeef699ee41386223bac8751308d7e901576ae5592d285c719ca` |

Task 0.5 adds matching runtime hash locks and stages these files as immutable
history. It does not modify their bytes.
