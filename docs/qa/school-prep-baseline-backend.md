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
