# School Prep Phase 0-1 Implementation Plan

> **Superseded 2026-07-13:** This historical plan is not executable authority. Use `docs/superpowers/plans/2026-07-13-school-prep-canonical-rebuild.md` under the approved canonical architecture contract.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first verified School Prep rebuild layer: official `/school` entry, old school route quarantine, versioned school onboarding profile, and backend-owned `/school/state`.

**Architecture:** The frontend renders one backend-owned next action from `GET /school/state`. The current `/subjects/*` school surfaces are removed from learner navigation before placement work begins. School onboarding gets its own versioned profile model so placement never depends on free-text learning goals again.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy text queries, Postgres/Supabase migrations, in-memory hardening store, Next.js App Router, TypeScript, existing `apiFetch`, Playwright/browser QA after implementation.

---

## Source Documents

- Architecture contract: `BUILD/Zidd-Backend/docs/school-prep-rebuild-architecture-contract.md`
- Spike evidence: `BUILD/Zidd-Backend/docs/school-prep-rebuild-spike-results.md`
- Current audit: `validation/school-prep-current-product-audit.md`

## File Structure

Backend create:

- `BUILD/Zidd-Backend/app/api/school_rebuild_routes.py` - new `/school/state` and `/school/onboarding` endpoints.
- `BUILD/Zidd-Backend/app/services/school_rebuild_state.py` - pure state-to-next-action service.
- `BUILD/Zidd-Backend/app/services/school_rebuild_profile.py` - validation and public serialization helpers for school profiles.
- `BUILD/Zidd-Backend/app/db/migrations/2026-07-10-school-rebuild-profile.sql` - versioned profile table.
- `BUILD/Zidd-Backend/tests/hardening/test_school_rebuild_phase_0_1_contract.py` - backend API/state/profile tests.

Backend modify:

- `BUILD/Zidd-Backend/app/main.py` - include `school_rebuild_routes.router` before legacy `school_routes`.
- `BUILD/Zidd-Backend/app/db/schema.sql` - add the same table/constraints as the migration.
- `BUILD/Zidd-Backend/app/db/repo.py` - add school profile version CRUD.
- `BUILD/Zidd-Backend/app/storage/pg_store.py` - expose repo methods.
- `BUILD/Zidd-Backend/tests/conftest.py` - add in-memory school profile version methods.
- `BUILD/Zidd-Backend/app/api/onboarding_routes.py` - change school motive destination from `/subjects` to `/school` and accept old minimal school profile only as draft seed.
- `BUILD/Zidd-Backend/app/api/me_routes.py` - route school users to `/school`.
- Existing onboarding tests in `BUILD/Zidd-Backend/tests/hardening/test_onboarding_profile_contract.py` must be updated from "class is not stored" to "global onboarding routes school users to `/school`; full class is stored only in school profile version."

Frontend create:

- `BUILD/Zidd-Frontend/src/services/schoolRebuild.ts` - typed client for `/school/state` and `/school/onboarding`.
- `BUILD/Zidd-Frontend/src/app/school/page.tsx` - calm backend-state shell.
- `BUILD/Zidd-Frontend/src/app/school/onboarding/page.tsx` - five-step school onboarding.
- `BUILD/Zidd-Frontend/scripts/check-school-rebuild-surface.mjs` - static UI contract check.

Frontend modify:

- `BUILD/Zidd-Frontend/package.json` - add `test:school-rebuild-surface`.
- `BUILD/Zidd-Frontend/src/services/me.ts` - school home/path route becomes `/school`.
- `BUILD/Zidd-Frontend/src/services/onboarding.ts` - school motive completion expects `/school`.
- `BUILD/Zidd-Frontend/src/app/onboarding/page.tsx` - send school users to `/school`, not `/subjects`.
- `BUILD/Zidd-Frontend/src/app/subjects/page.tsx` - redirect learner traffic to `/school` or remove school cards.
- `BUILD/Zidd-Frontend/src/app/subjects/v3/page.tsx` - redirect learner traffic to `/school`; keep internal-only if needed.
- `BUILD/Zidd-Frontend/src/app/subjects/v2/page.tsx` - internal-only banner or redirect.
- `BUILD/Zidd-Frontend/src/app/subjects/class/[classNo]/page.tsx` - redirect learner traffic to `/school`.
- `BUILD/Zidd-Frontend/src/app/subjects/test/[testId]/page.tsx` - no learner school entry; keep direct legacy continuity only if required.
- `BUILD/Zidd-Frontend/src/app/(gamified)/map/page.tsx` - school module redirects to `/school`.
- `BUILD/Zidd-Frontend/src/app/career/page.tsx` - school motive redirects to `/school`.
- `BUILD/Zidd-Frontend/src/app/profile/page.tsx` - school action links to `/school`.
- `BUILD/Zidd-Frontend/src/components/shared/AppHeader.tsx` - active home logic uses `/school`.
- `BUILD/Zidd-Frontend/src/middleware.ts` - update protected/redirect behavior if it hardcodes `/subjects`.

---

## Task 1: Backend Contract Tests First

**Files:**
- Create: `BUILD/Zidd-Backend/tests/hardening/test_school_rebuild_phase_0_1_contract.py`

- [ ] **Step 1: Add failing tests for school state and profile contract**

Use this test file shape:

```python
import asyncio

from fastapi.testclient import TestClient

from app.main import app

AUTH = {"Authorization": "Bearer test_token"}


def _run(coro):
    return asyncio.run(coro)


def _valid_school_profile():
    return {
        "display_name": "Open Assets",
        "school_name": "Open Assets Test School",
        "board_id": "cbse",
        "target_class_no": 3,
        "subject_ids": ["english"],
        "preferred_teaching_language": "hi_en",
        "english_comfort": "medium",
        "learner_goal": "I want to understand Class 3 English chapters.",
        "parent_goal": "Build confidence without memorising answers.",
        "prior_difficulty_signals": ["vocabulary", "chapter_answers"],
    }


def test_school_state_routes_profile_missing_to_school_onboarding(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    _run(store.complete_onboarding(
        user_id="test_user",
        display_name="Open Assets",
        primary_motive="school",
        school_profile={"school_name": "Old School"},
        career_profile={},
    ))

    client = TestClient(app)
    response = client.get("/school/state", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["profile_status"] == "missing"
    assert response.json()["next_action"] == "complete_profile"
    assert response.json()["next_action_url"] == "/school/onboarding"
    assert response.json()["unlock_state"] == "locked"


def test_school_onboarding_complete_creates_active_profile_version(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)

    response = client.post("/school/onboarding/complete", headers=AUTH, json=_valid_school_profile())

    assert response.status_code == 200
    body = response.json()
    assert body["profile_status"] == "complete"
    assert body["profile"]["target_class_no"] == 3
    assert body["profile"]["subject_ids"] == ["english"]
    assert body["profile"]["preferred_teaching_language"] == "hi_en"
    assert body["profile"]["profile_version_id"]

    state = client.get("/school/state", headers=AUTH).json()
    assert state["profile_status"] == "complete"
    assert state["target_class_no"] == 3
    assert state["subject_id"] == "english"
    assert state["next_action"] == "start_placement"
    assert state["next_action_url"] == "/school/placement"


def test_school_onboarding_rejects_incomplete_profile(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)
    payload = _valid_school_profile()
    payload.pop("target_class_no")

    response = client.post("/school/onboarding/complete", headers=AUTH, json=payload)

    assert response.status_code == 422


def test_global_school_onboarding_routes_to_school_not_subjects(store):
    _run(store.ensure_profile("test_user", name="Open Assets", email="open@example.com"))
    client = TestClient(app)

    response = client.post(
        "/onboarding/complete",
        headers=AUTH,
        json={
            "display_name": "Open Assets",
            "primary_motive": "school",
            "school_profile": {"school_name": "Open Assets Test School"},
        },
    )

    assert response.status_code == 200
    assert response.json()["destination"] == "/school"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd BUILD/Zidd-Backend
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py -q
```

Expected: FAIL because `/school/state`, `/school/onboarding/complete`, and school profile version persistence do not exist.

---

## Task 2: Add Versioned School Profile Persistence

**Files:**
- Create: `BUILD/Zidd-Backend/app/db/migrations/2026-07-10-school-rebuild-profile.sql`
- Modify: `BUILD/Zidd-Backend/app/db/schema.sql`
- Modify: `BUILD/Zidd-Backend/app/db/repo.py`
- Modify: `BUILD/Zidd-Backend/app/storage/pg_store.py`
- Modify: `BUILD/Zidd-Backend/tests/conftest.py`

- [ ] **Step 1: Add migration and schema table**

Add this table to the migration and mirror it in `schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS public.school_profile_versions (
    profile_version_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
    display_name TEXT NOT NULL DEFAULT '',
    school_name TEXT NOT NULL,
    board_id TEXT NOT NULL,
    target_class_no INTEGER NOT NULL CHECK (target_class_no BETWEEN 2 AND 5),
    subject_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_teaching_language TEXT NOT NULL CHECK (preferred_teaching_language IN ('en', 'hi', 'hi_en')),
    english_comfort TEXT NOT NULL CHECK (english_comfort IN ('low', 'medium', 'high')),
    learner_goal TEXT NOT NULL DEFAULT '',
    parent_goal TEXT NOT NULL DEFAULT '',
    prior_difficulty_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_one_active
    ON public.school_profile_versions(user_id)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_school_profile_versions_user_status_updated
    ON public.school_profile_versions(user_id, status, updated_at DESC);

ALTER TABLE public.school_profile_versions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_profile_versions FROM anon;
REVOKE ALL ON TABLE public.school_profile_versions FROM authenticated;
REVOKE ALL ON TABLE public.school_profile_versions FROM PUBLIC;
```

- [ ] **Step 2: Add repo methods**

Add these functions to `app/db/repo.py`:

```python
async def get_active_school_profile_version(session: AsyncSession, user_id: str) -> dict | None:
    result = await session.execute(
        text("""
            SELECT *
            FROM school_profile_versions
            WHERE user_id = :uid AND status = 'active'
            ORDER BY activated_at DESC NULLS LAST, updated_at DESC
            LIMIT 1
        """),
        {"uid": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def save_school_profile_version(
    session: AsyncSession,
    *,
    profile_version_id: str,
    user_id: str,
    status: str,
    profile: dict,
) -> dict:
    await session.execute(
        text("""
            UPDATE school_profile_versions
            SET status = 'archived', archived_at = now(), updated_at = now()
            WHERE user_id = :uid AND status = 'active' AND :status = 'active'
        """),
        {"uid": user_id, "status": status},
    )
    result = await session.execute(
        text("""
            INSERT INTO school_profile_versions
                (profile_version_id, user_id, status, display_name, school_name,
                 board_id, target_class_no, subject_ids, preferred_teaching_language,
                 english_comfort, learner_goal, parent_goal, prior_difficulty_signals,
                 activated_at)
            VALUES
                (CAST(:profile_version_id AS uuid), :user_id, :status, :display_name,
                 :school_name, :board_id, :target_class_no, CAST(:subject_ids AS jsonb),
                 :preferred_teaching_language, :english_comfort, :learner_goal,
                 :parent_goal, CAST(:prior_difficulty_signals AS jsonb),
                 CASE WHEN :status = 'active' THEN now() ELSE NULL END)
            RETURNING *
        """),
        {
            "profile_version_id": profile_version_id,
            "user_id": user_id,
            "status": status,
            "display_name": profile["display_name"],
            "school_name": profile["school_name"],
            "board_id": profile["board_id"],
            "target_class_no": profile["target_class_no"],
            "subject_ids": json.dumps(profile["subject_ids"]),
            "preferred_teaching_language": profile["preferred_teaching_language"],
            "english_comfort": profile["english_comfort"],
            "learner_goal": profile["learner_goal"],
            "parent_goal": profile["parent_goal"],
            "prior_difficulty_signals": json.dumps(profile["prior_difficulty_signals"]),
        },
    )
    row = result.mappings().first()
    await session.commit()
    return dict(row)
```

- [ ] **Step 3: Expose methods in `PgStore` and `InMemoryStore`**

Add matching async methods:

```python
async def get_active_school_profile_version(self, user_id: str) -> dict | None:
    from app.db import repo
    async with _session() as s:
        return await repo.get_active_school_profile_version(s, user_id)


async def save_school_profile_version(self, *, profile_version_id: str, user_id: str, status: str, profile: dict) -> dict:
    from app.db import repo
    async with _session() as s:
        return await repo.save_school_profile_version(
            s,
            profile_version_id=profile_version_id,
            user_id=user_id,
            status=status,
            profile=profile,
        )
```

For `InMemoryStore`, add `self.school_profile_versions = {}` and implement the same behavior with one active profile per user.

- [ ] **Step 4: Run backend contract tests again**

Run:

```bash
cd BUILD/Zidd-Backend
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py -q
```

Expected: still FAIL because API endpoints are not implemented yet, but persistence helper errors should be gone once routes call them.

---

## Task 3: Add School Profile Validation And `/school/state`

**Files:**
- Create: `BUILD/Zidd-Backend/app/services/school_rebuild_profile.py`
- Create: `BUILD/Zidd-Backend/app/services/school_rebuild_state.py`
- Create: `BUILD/Zidd-Backend/app/api/school_rebuild_routes.py`
- Modify: `BUILD/Zidd-Backend/app/main.py`

- [ ] **Step 1: Add profile validation helper**

Create `school_rebuild_profile.py`:

```python
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SchoolRebuildProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=2, max_length=120)
    school_name: str = Field(min_length=2, max_length=160)
    board_id: Literal["cbse", "ncert"] = "cbse"
    target_class_no: int = Field(ge=2, le=5)
    subject_ids: list[Literal["english"]] = Field(default_factory=lambda: ["english"], min_length=1)
    preferred_teaching_language: Literal["en", "hi", "hi_en"]
    english_comfort: Literal["low", "medium", "high"]
    learner_goal: str = Field(default="", max_length=360)
    parent_goal: str = Field(default="", max_length=360)
    prior_difficulty_signals: list[
        Literal["reading", "vocabulary", "grammar", "writing", "chapter_answers"]
    ] = Field(default_factory=list, max_length=5)


def public_school_profile(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile_version_id": str(row["profile_version_id"]),
        "display_name": row.get("display_name") or "",
        "school_name": row.get("school_name") or "",
        "board_id": row.get("board_id") or "cbse",
        "target_class_no": int(row.get("target_class_no") or 0),
        "subject_ids": list(row.get("subject_ids") or []),
        "preferred_teaching_language": row.get("preferred_teaching_language") or "en",
        "english_comfort": row.get("english_comfort") or "medium",
        "learner_goal": row.get("learner_goal") or "",
        "parent_goal": row.get("parent_goal") or "",
        "prior_difficulty_signals": list(row.get("prior_difficulty_signals") or []),
    }
```

- [ ] **Step 2: Add state service**

Create `school_rebuild_state.py`:

```python
def school_state_for_profile(*, learner_profile: dict, school_profile: dict | None) -> dict:
    if learner_profile.get("primary_motive") != "school" or not school_profile:
        return {
            "profile_status": "missing",
            "target_class_no": None,
            "subject_id": None,
            "profile_version_id": None,
            "active_flow": "onboarding",
            "active_session_id": None,
            "placement_status": "not_started",
            "unlock_state": "locked",
            "evaluated_class_no": None,
            "active_learning_class_no": None,
            "next_action": "complete_profile",
            "next_action_url": "/school/onboarding",
            "learner_message": "Set up school prep before your readiness check.",
            "parent_message": "We need class, subject, and language details before testing readiness.",
            "blocked_reason": None,
        }
    subject_id = (school_profile.get("subject_ids") or ["english"])[0]
    return {
        "profile_status": "complete",
        "target_class_no": school_profile["target_class_no"],
        "subject_id": subject_id,
        "profile_version_id": str(school_profile["profile_version_id"]),
        "active_flow": "none",
        "active_session_id": None,
        "placement_status": "not_started",
        "unlock_state": "locked",
        "evaluated_class_no": None,
        "active_learning_class_no": None,
        "next_action": "start_placement",
        "next_action_url": "/school/placement",
        "learner_message": "Start your readiness check when you are ready.",
        "parent_message": "The next step is a readiness check, not a chapter lesson.",
        "blocked_reason": None,
    }
```

- [ ] **Step 3: Add API routes**

Create `school_rebuild_routes.py`:

```python
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.services.school_rebuild_profile import SchoolRebuildProfileIn, public_school_profile
from app.services.school_rebuild_state import school_state_for_profile
from app.storage import get_storage

router = APIRouter(prefix="/school", tags=["school-rebuild"])


def _uid(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    return user_id


async def _learner_profile(user_id: str) -> dict:
    profile = await get_storage().get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=401, detail="Profile not found; sign in again")
    return profile


@router.get("/state")
async def school_state(request: Request) -> dict:
    user_id = _uid(request)
    learner = await _learner_profile(user_id)
    school_profile = await get_storage().get_active_school_profile_version(user_id)
    public_profile = public_school_profile(school_profile) if school_profile else None
    return school_state_for_profile(learner_profile=learner, school_profile=public_profile)


@router.get("/onboarding")
async def school_onboarding(request: Request) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    active = await get_storage().get_active_school_profile_version(user_id)
    return {"profile": public_school_profile(active) if active else None}


@router.post("/onboarding/complete")
async def complete_school_onboarding(req: SchoolRebuildProfileIn, request: Request) -> dict:
    user_id = _uid(request)
    await _learner_profile(user_id)
    profile = req.model_dump()
    saved = await get_storage().save_school_profile_version(
        profile_version_id=str(uuid4()),
        user_id=user_id,
        status="active",
        profile=profile,
    )
    public = public_school_profile(saved)
    return {"profile_status": "complete", "profile": public}
```

- [ ] **Step 4: Register router**

In `main.py`, import and include before the legacy school router:

```python
from app.api.school_rebuild_routes import router as school_rebuild_router

app.include_router(school_rebuild_router)
app.include_router(school_router)
```

- [ ] **Step 5: Run backend tests**

Run:

```bash
cd BUILD/Zidd-Backend
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py -q
```

Expected: PASS except the global onboarding destination test until Task 4 updates legacy onboarding routes.

---

## Task 4: Route Existing School Motive To `/school`

**Files:**
- Modify: `BUILD/Zidd-Backend/app/api/onboarding_routes.py`
- Modify: `BUILD/Zidd-Backend/app/api/me_routes.py`
- Modify: `BUILD/Zidd-Backend/tests/hardening/test_onboarding_profile_contract.py`

- [ ] **Step 1: Change backend destination helper**

In `onboarding_routes.py`, change:

```python
def _destination(primary_motive: str) -> str:
    return "/school" if primary_motive == "school" else "/career"
```

- [ ] **Step 2: Keep minimal legacy school profile as seed only**

Do not add `class_no` to old `SchoolProfileIn`. Full class/language lives in `/school/onboarding`.

- [ ] **Step 3: Change `/me/gate` school home**

In `me_routes.py`, change the school branch of `_home_for_profile` to return `/school`.

- [ ] **Step 4: Update old tests**

Rename `test_school_onboarding_does_not_store_class_and_routes_to_subjects` to `test_global_school_onboarding_routes_to_school_and_defers_class_to_school_profile`.

Expected assertions:

```python
assert response.json()["destination"] == "/school"
assert body["home"] == "/school"
assert "class_no" not in body["school_profile"]
```

- [ ] **Step 5: Run focused backend tests**

Run:

```bash
cd BUILD/Zidd-Backend
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py tests/hardening/test_onboarding_profile_contract.py -q
```

Expected: PASS.

---

## Task 5: Frontend Service Types

**Files:**
- Create: `BUILD/Zidd-Frontend/src/services/schoolRebuild.ts`
- Modify: `BUILD/Zidd-Frontend/src/services/me.ts`
- Modify: `BUILD/Zidd-Frontend/src/services/onboarding.ts`

- [ ] **Step 1: Add typed service client**

Create `schoolRebuild.ts`:

```ts
import { apiFetch, getAuthCacheKey } from '@/services/api';

export type TeachingLanguage = 'en' | 'hi' | 'hi_en';
export type EnglishComfort = 'low' | 'medium' | 'high';
export type SchoolNextAction =
  | 'complete_profile'
  | 'start_placement'
  | 'resume_placement'
  | 'view_placement_report'
  | 'start_recap'
  | 'resume_recap'
  | 'start_curriculum'
  | 'resume_curriculum'
  | 'resume_masterclass'
  | 'view_report';

export interface SchoolProfileInput {
  display_name: string;
  school_name: string;
  board_id: 'cbse' | 'ncert';
  target_class_no: number;
  subject_ids: ['english'];
  preferred_teaching_language: TeachingLanguage;
  english_comfort: EnglishComfort;
  learner_goal: string;
  parent_goal: string;
  prior_difficulty_signals: Array<'reading' | 'vocabulary' | 'grammar' | 'writing' | 'chapter_answers'>;
}

export interface SchoolState {
  profile_status: 'missing' | 'incomplete' | 'complete';
  target_class_no: number | null;
  subject_id: string | null;
  profile_version_id: string | null;
  active_flow: string;
  active_session_id: string | null;
  placement_status: string;
  unlock_state: 'locked' | 'recap_required' | 'target_unlocked';
  evaluated_class_no: number | null;
  active_learning_class_no: number | null;
  next_action: SchoolNextAction | null;
  next_action_url: string;
  learner_message: string;
  parent_message: string;
  blocked_reason: string | null;
}

let cachedState: { authKey: string; value: SchoolState; expiresAt: number } | null = null;
const SCHOOL_STATE_CACHE_MS = 5_000;

export function invalidateSchoolRebuildCache() {
  cachedState = null;
}

export async function getSchoolState(): Promise<SchoolState> {
  const authKey = await getAuthCacheKey();
  const now = Date.now();
  if (cachedState && cachedState.authKey === authKey && cachedState.expiresAt > now) {
    return cachedState.value;
  }
  const value = await apiFetch('/school/state');
  cachedState = { authKey, value, expiresAt: Date.now() + SCHOOL_STATE_CACHE_MS };
  return value;
}

export async function completeSchoolOnboarding(profile: SchoolProfileInput) {
  const result = await apiFetch('/school/onboarding/complete', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
  invalidateSchoolRebuildCache();
  return result;
}
```

- [ ] **Step 2: Route school users to `/school`**

In `me.ts`, change `homeForMe` and `myPathForMe` school branches to `/school`.

- [ ] **Step 3: Update onboarding destination assumptions**

In `onboarding.ts`, keep the backend response as source of truth; do not hardcode `/subjects` anywhere.

- [ ] **Step 4: Run TypeScript**

Run:

```bash
cd BUILD/Zidd-Frontend
npx tsc --noEmit
```

Expected: PASS after page code is added in later tasks; at this step it may fail only if imports are unused.

---

## Task 6: Build `/school` Shell

**Files:**
- Create: `BUILD/Zidd-Frontend/src/app/school/page.tsx`

- [ ] **Step 1: Implement the backend-state shell**

Create a client page that:

- calls `getSchoolState()`;
- renders loading, error, and one next-action panel;
- has no class cards;
- has no V2/V3 wording;
- routes a primary CTA using `router.push(state.next_action_url)` only when
  `state.next_action` is non-null and authorized by `allowed_next_actions`.

Required visible state mapping:

```ts
const actionLabel: Record<SchoolNextAction, string> = {
  complete_profile: 'Set up school prep',
  start_placement: 'Start readiness check',
  resume_placement: 'Continue readiness check',
  view_placement_report: 'View readiness report',
  start_recap: 'Start recap path',
  resume_recap: 'Continue recap',
  start_curriculum: 'Start target class',
  resume_curriculum: 'Continue class',
  resume_masterclass: 'Continue masterclass',
  view_report: 'View report',
};
```

- [ ] **Step 2: Add state hygiene**

The page must not include these strings:

```text
School V2
School V3
ENGINEERING_SEED
answer_key
model_answer
rubric
/subjects/v2
/subjects/v3
```

- [ ] **Step 3: Run TypeScript**

Run:

```bash
cd BUILD/Zidd-Frontend
npx tsc --noEmit
```

Expected: PASS after imports and types are consistent.

---

## Task 7: Build `/school/onboarding`

**Files:**
- Create: `BUILD/Zidd-Frontend/src/app/school/onboarding/page.tsx`

- [ ] **Step 1: Implement five steps**

Step fields:

1. learner display name, school name;
2. board/curriculum, target class, subject;
3. teaching language, English comfort;
4. learner/parent goal, prior difficulty signals;
5. review and confirm.

Use fixed options:

```ts
const classOptions = [2, 3, 4, 5];
const languageOptions = [
  { value: 'en', label: 'English' },
  { value: 'hi_en', label: 'Hinglish' },
  { value: 'hi', label: 'Hindi support' },
] as const;
const difficultySignals = [
  'reading',
  'vocabulary',
  'grammar',
  'writing',
  'chapter_answers',
] as const;
```

- [ ] **Step 2: Save only on confirm**

On final confirm:

```ts
await completeSchoolOnboarding({
  display_name: displayName.trim(),
  school_name: schoolName.trim(),
  board_id: 'cbse',
  target_class_no: targetClassNo,
  subject_ids: ['english'],
  preferred_teaching_language: language,
  english_comfort: englishComfort,
  learner_goal: learnerGoal.trim(),
  parent_goal: parentGoal.trim(),
  prior_difficulty_signals: selectedSignals,
});
router.replace('/school');
```

- [ ] **Step 3: Enforce UI rules**

Each step must have:

- one primary CTA;
- back button except first step;
- inline field errors;
- disabled saving state;
- no nested cards;
- mobile-safe layout.

- [ ] **Step 4: Run TypeScript**

Run:

```bash
cd BUILD/Zidd-Frontend
npx tsc --noEmit
```

Expected: PASS.

---

## Task 8: Quarantine Old School Routes

**Files:**
- Modify: `BUILD/Zidd-Frontend/src/app/subjects/page.tsx`
- Modify: `BUILD/Zidd-Frontend/src/app/subjects/v2/page.tsx`
- Modify: `BUILD/Zidd-Frontend/src/app/subjects/v3/page.tsx`
- Modify: `BUILD/Zidd-Frontend/src/app/subjects/class/[classNo]/page.tsx`
- Modify: `BUILD/Zidd-Frontend/src/app/subjects/test/[testId]/page.tsx`
- Modify: `BUILD/Zidd-Frontend/src/app/(gamified)/map/page.tsx`
- Modify: `BUILD/Zidd-Frontend/src/app/career/page.tsx`
- Modify: `BUILD/Zidd-Frontend/src/app/profile/page.tsx`
- Modify: `BUILD/Zidd-Frontend/src/components/shared/AppHeader.tsx`
- Modify: `BUILD/Zidd-Frontend/src/middleware.ts`

- [ ] **Step 1: Redirect learner school entries**

Use `router.replace('/school')` for client pages or `redirect('/school')` for server pages where applicable.

Minimum required changes:

- `/subjects` no longer renders V2/V3/legacy cards for normal learners.
- `/subjects/v3` redirects to `/school`.
- `/subjects/v2` redirects to `/school` unless an internal flag is explicitly added later.
- legacy class/test pages are not linked from learner school prep.

- [ ] **Step 2: Update routing helpers**

Update all school branches discovered by the spike:

```text
src/services/me.ts
src/app/(gamified)/map/page.tsx
src/app/career/page.tsx
src/app/profile/page.tsx
src/components/shared/AppHeader.tsx
src/middleware.ts
```

- [ ] **Step 3: Do not delete legacy code yet**

Keep old pages present for comparison until Phase 0 QA passes, but remove them from learner navigation.

---

## Task 9: Static Frontend Contract Check

**Files:**
- Create: `BUILD/Zidd-Frontend/scripts/check-school-rebuild-surface.mjs`
- Modify: `BUILD/Zidd-Frontend/package.json`

- [ ] **Step 1: Add script**

Create:

```js
import fs from 'node:fs';

const requiredFiles = [
  'src/app/school/page.tsx',
  'src/app/school/onboarding/page.tsx',
  'src/services/schoolRebuild.ts',
];
for (const file of requiredFiles) {
  if (!fs.existsSync(file)) throw new Error(`Missing ${file}`);
}

const schoolPage = fs.readFileSync('src/app/school/page.tsx', 'utf8');
const onboardingPage = fs.readFileSync('src/app/school/onboarding/page.tsx', 'utf8');
const meService = fs.readFileSync('src/services/me.ts', 'utf8');
const subjectsPage = fs.readFileSync('src/app/subjects/page.tsx', 'utf8');

for (const token of ['getSchoolState', 'next_action', 'Start readiness check']) {
  if (!schoolPage.includes(token)) throw new Error(`/school page missing ${token}`);
}
for (const token of ['target_class_no', 'preferred_teaching_language', 'english_comfort']) {
  if (!onboardingPage.includes(token)) throw new Error(`/school/onboarding missing ${token}`);
}
for (const forbidden of ['School V2', 'School V3', 'ENGINEERING_SEED', 'answer_key', 'model_answer', 'rubric']) {
  if (schoolPage.includes(forbidden) || onboardingPage.includes(forbidden)) {
    throw new Error(`School rebuild surface leaks forbidden token ${forbidden}`);
  }
}
if (!meService.includes("return '/school'")) {
  throw new Error('School home route must resolve to /school');
}
if (subjectsPage.includes('/subjects/v3') || subjectsPage.includes('/subjects/v2')) {
  throw new Error('/subjects must not link to V2/V3 learner surfaces');
}

console.log('School rebuild frontend surface check passed');
```

- [ ] **Step 2: Add package script**

In `package.json`:

```json
"test:school-rebuild-surface": "node scripts/check-school-rebuild-surface.mjs"
```

- [ ] **Step 3: Run frontend checks**

Run:

```bash
cd BUILD/Zidd-Frontend
npm run test:school-rebuild-surface
npx tsc --noEmit
npm run lint
```

Expected: all PASS.

---

## Task 10: Phase 0/1 Verification And QA Report

**Files:**
- Create: `QA_RUNS/school-rebuild-phase-0-1-YYYYMMDD-HHMM/report.md`

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd BUILD/Zidd-Backend
pytest tests/hardening/test_school_rebuild_phase_0_1_contract.py tests/hardening/test_onboarding_profile_contract.py -q
```

Expected: PASS.

- [ ] **Step 2: Run frontend tests**

Run:

```bash
cd BUILD/Zidd-Frontend
npm run test:school-rebuild-surface
npx tsc --noEmit
npm run lint
```

Expected: PASS.

- [ ] **Step 3: Live browser QA**

Use `[SCHOOL_QA_ACCOUNT]`, not `ryuk9525@gmail.com`.

Browser QA sequence:

1. Reset only `[SCHOOL_QA_ACCOUNT]` school rows.
2. Open `http://localhost:3001/school`.
3. Confirm missing profile state shows one CTA: "Set up school prep".
4. Complete `/school/onboarding` for Class 3, English, Hinglish.
5. Confirm backend DB stores all required fields.
6. Reload `/school`.
7. Confirm one CTA: "Start readiness check".
8. Visit `/subjects`, `/subjects/v2`, `/subjects/v3`, `/subjects/class/3`; confirm learner is redirected or clearly not in old learner school flow.
9. Capture desktop and mobile screenshots.

- [ ] **Step 4: QA report contents**

The report must include:

- account used;
- rows reset;
- backend API responses for `/school/state`;
- DB proof for school profile version;
- screenshots list;
- route quarantine result table;
- frontend/backend commands run;
- issues found;
- fixes applied;
- retest result.

---

## Self-Review Checklist

- Spec coverage: This plan covers only Phase 0 and Phase 1 from the architecture contract. Placement, content bank, recap, masterclass, curriculum, reports, and parent view are intentionally excluded.
- No old school route can remain as primary learner entry after Task 8.
- `/school/state` is backend-owned before any placement work begins.
- School profile stores target class, subject, language, English comfort, goals, and difficulty signals before placement.
- The first browser QA happens before placement implementation.
- No task asks the frontend to infer unlock, readiness, or curriculum access.
