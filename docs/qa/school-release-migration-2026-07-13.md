---
created: 2026-07-13
project: zidd
ecosystem: full-stack
tags: [school-prep, supabase, migration, qa]
---

# School Release Authority Migration QA

Backlinks: [[docs/qa/school-prep-baseline-backend]] [[docs/superpowers/plans/2026-07-13-school-prep-canonical-rebuild]]

## Disposable PostgreSQL

- Container: PostgreSQL 16, loopback-only, disposable database name guard enabled.
- Integration result: `31 passed`, zero skips.
- Reviewer rerun: `54 passed` across migration and schema authority coverage.
- Covered empty bootstrap, upgraded copy, public ordered apply, exact rerun,
  marker hash mismatch, selective lineage, foreign keys, release immutability,
  RLS, revoked grants, preflight failure rollback, and schema guard.
- The disposable container was removed after verification.

## Supabase Preflight

- Result: PASS.
- Active School profiles: 1.
- Active School sessions: 1.
- Active School placement reports: 1.
- Rebuild session lineage candidates: 6.
- Rebuild report lineage candidates: 1.
- Ambiguous sessions/reports: 0/0.
- Duplicate approved release mappings: 0.
- Required predecessor tables, constraints, and active-flow index: valid.
- Protected evidence:
  - `/tmp/zidd-school-preflight-live-20260713.json`
  - `/tmp/zidd-school-preflight-apply-live-20260713.json`
  - `/tmp/zidd-school-preflight-reapply-live-20260713.json`
- Evidence files are mode `0600`; learner-linked IDs are not copied into Git.

## Live Apply

- Applied only `2026-07-13-001-school-release-authority.sql` through
  `scripts/apply_migrations.py` after the passing preflight.
- Reapplied the same file through the hash-locked runner; the marker made the
  SQL idempotent and runtime schema validation passed.
- Independent post-apply `validate_runtime_schema()` result:
  `live_school_schema_guard_ok`.
- Canonical release manifest digest:
  `4176645667f79edb3cc07ab42dee10771c7cc631aabc0ba1fa4da9cab5a6eeea`.
