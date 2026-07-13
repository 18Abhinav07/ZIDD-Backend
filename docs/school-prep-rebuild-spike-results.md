# School Prep Rebuild Spike Results - 2026-07-10

Architecture contract: `BUILD/Zidd-Backend/docs/school-prep-rebuild-architecture-contract.md`

## Assumption 1: Old school routes can be quarantined behind `/school`

- File: `validation/spike-1-school-route-quarantine.py`
- Result: PASS
- Evidence:
  - `old_school_route_files= 9`
  - `BUILD/Zidd-Frontend/src/app/subjects/page.tsx /subjects,/subjects/v2,/subjects/v3,/subjects/class`
  - `BUILD/Zidd-Frontend/src/app/subjects/class/[classNo]/page.tsx /subjects,/subjects/test`
  - `BUILD/Zidd-Frontend/src/services/me.ts /subjects`
  - `BUILD/Zidd-Frontend/src/components/shared/AppHeader.tsx /subjects`
  - `PASS route quarantine scope is discoverable and must be redirected/rewired`
- Impact: Phase 0 can be planned with a concrete redirect/link-removal scope. The implementation must touch the `/subjects` route tree, motive home routing, map/profile redirects, header active-state logic, and middleware.
- Note: The first run failed because the spike incorrectly expected V2/V3 route files to contain their own route strings. The corrected spike checks route file existence separately from link references.

## Assumption 2: Current school onboarding profile is insufficient and needs a versioned profile model

- File: `validation/spike-2-school-profile-contract.py`
- Result: PASS
- Evidence:
  - `SchoolProfileIn fields= school_name,learning_goal`
  - `missing_required_fields= board_id,english_comfort,learner_goal,parent_goal,preferred_teaching_language,prior_difficulty_signals,subject_ids,target_class_no`
  - `has_versioned_school_profile_table= False`
  - `PASS current profile model is insufficient; Phase 1 needs versioned school profile`
- Impact: Phase 1 must add a real `school_profiles` or `school_profile_versions` persistence contract before placement can start. The current onboarding profile cannot power personalized placement.
- Note: The first run failed because the SQL detector was too broad and matched existing JSON `school_profile` fields. The corrected detector checks only dedicated `school_profiles` or `school_profile_versions` tables.

## Assumption 3: Current V3 placement/path/curriculum APIs allow client-shaped unlocks

- File: `validation/spike-3-school-state-gating.py`
- Result: PASS
- Evidence:
  - `backend_path_accepts_weak_skill_ids=True`
  - `backend_path_accepts_nonblocking=True`
  - `backend_curriculum_accepts_chapter=True`
  - `backend_curriculum_accepts_watchlist=True`
  - `frontend_derives_path_from_weak_ids=True`
  - `frontend_calls_curriculum_with_chapter=True`
  - `service_posts_v3_path=True`
  - `service_posts_v3_curriculum_start=True`
  - `PASS current V3 allows client-shaped path/curriculum starts; /school/state gate is required`
- Impact: Phase 0/1 implementation must introduce backend-owned `/school/state` and cannot reuse the current V3 path/curriculum start shape as the learner-facing contract.

## Gate Decision

ALL PASS after correcting two spike assertion bugs. Architecture empirically validated for writing the Phase 0/1 implementation plan. The implementation plan must explicitly include:

- `/school` state API and state-to-CTA tests.
- Route quarantine for all nine discovered old-route reference files.
- Versioned school profile persistence before placement.
- Backend-owned unlock and next-action semantics before any curriculum or recap route.
