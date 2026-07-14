# Career/School Integration Attestation

Repository: `ZIDD-Backend`

- Frozen Career parent: `25a5d4bc878e42455587231bf8c04058cde670d0`
- Frozen School parent: `e0e63b3b6750e96842dfc7b6147d939b501a6e0e`
- Merge base: `ee7a4b3ddf1a4733a112fc3f38c7cb2b3f542a0f`
- Resolved core tree: `f873c41417f2bd962391354b3b8865ad436c1f53`
- Ownership rows: `275`
- Manual/integration patch paths: `44`
- Manifest SHA-256: `7691cb808eddd5087613eb8e4b1dbbe8e369a514f8dfa66d5483f0d9fe1fd8db`
- Patch SHA-256: `2243dd00ade2edf11a3adb8d41d71c1da01f4009d8c09a49d55237041ed41428`

The ownership manifest covers every path changed by the frozen School parent and
every resolved application path that differs from the frozen Career parent.
Attestation metadata under this directory is excluded from the core tree to
avoid recursive self-hashing; `manifest.lock` binds the manifest and patch.

Reproduce from a clean clone:

```bash
python3 scripts/reproduce_career_school_integration.py   --career 25a5d4bc878e42455587231bf8c04058cde670d0   --school e0e63b3b6750e96842dfc7b6147d939b501a6e0e   --manifest docs/integration/2026-07-14-career-school/ownership-manifest.tsv   --patch docs/integration/2026-07-14-career-school/career-preimage.patch   --lock docs/integration/2026-07-14-career-school/manifest.lock
```
