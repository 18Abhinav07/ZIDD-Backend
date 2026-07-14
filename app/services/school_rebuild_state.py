from typing import Any

from app.services.school_rebuild_profile import (
    school_catalog_selection_available,
    school_coach_identity,
)


SCHOOL_HOME_URL = "/school"
SCHOOL_ONBOARDING_URL = "/school/onboarding"
SCHOOL_READINESS_URL = "/school/readiness"
SCHOOL_READINESS_REPORT_URL = "/school/readiness/report"
SCHOOL_RECAP_URL = "/school/recap"

ACTIVE_PLACEMENT_STATUSES = frozenset({"active", "paused_for_masterclass"})
ACTIVE_LINKED_SESSION_STATUSES = frozenset({"active", "paused_for_masterclass"})
ACTIVE_LINKED_SESSION_STATUS = "active"
PROCESSING_ANSWER_STATUS = "processing"
VALID_REPORT_TRANSITIONS = frozenset(
    {
        ("target_ready", "target_unlocked"),
        ("below_target", "recap_required"),
        ("insufficient_evidence", "locked"),
        ("abandoned", "locked"),
    }
)
ACTIVE_CURRICULUM_PHASES = frozenset(
    {"learning", "chapter_check", "remediation"}
)
CANONICAL_SCHOOL_NEXT_ACTIONS = frozenset(
    {
        "sign_in",
        "complete_profile",
        "edit_profile",
        "start_placement",
        "resume_placement",
        "finish_placement",
        "view_placement_report",
        "start_recap",
        "resume_recap",
        "revise_recap_path",
        "start_curriculum",
        "resume_curriculum",
        "start_masterclass",
        "resume_masterclass",
        "view_support_plan",
        "resume_support",
        "view_report",
        "retry",
    }
)


def unauthenticated_school_state() -> dict[str, Any]:
    return _build_state(
        profile_status="unauthenticated",
        target_class_no=None,
        subject_id=None,
        profile_version_id=None,
        preferred_teaching_language=None,
        coach_avatar_id=None,
        coach_palette_id=None,
        active_flow="none",
        active_session_id=None,
        placement_status="not_started",
        unlock_state="locked",
        evaluated_class_no=None,
        active_learning_class_no=None,
        status="needs_action",
        next_action="sign_in",
        next_action_url="/auth/login",
        allowed_next_actions=["sign_in"],
        learner_message="Sign in to continue your saved school path.",
        parent_message="School progress is available after sign-in.",
        blocked_reason=None,
    )


def _build_state(
    *,
    profile_status: str,
    target_class_no: int | None,
    subject_id: str | None,
    profile_version_id: str | None,
    preferred_teaching_language: str | None,
    coach_avatar_id: str | None,
    coach_palette_id: str | None,
    active_flow: str,
    active_session_id: str | None,
    placement_status: str,
    unlock_state: str,
    evaluated_class_no: int | None,
    active_learning_class_no: int | None,
    status: str,
    next_action: str | None,
    next_action_url: str,
    allowed_next_actions: list[str],
    learner_message: str,
    parent_message: str,
    blocked_reason: str | None,
) -> dict[str, Any]:
    invalid_allowed_actions = set(allowed_next_actions) - CANONICAL_SCHOOL_NEXT_ACTIONS
    if invalid_allowed_actions:
        raise ValueError("invalid_school_next_action")
    if not allowed_next_actions:
        if next_action is not None:
            raise ValueError("school_next_action_must_be_null")
    elif next_action not in allowed_next_actions:
        raise ValueError("school_next_action_not_allowed")

    return {
        "profile_status": profile_status,
        "target_class_no": target_class_no,
        "subject_id": subject_id,
        "profile_version_id": profile_version_id,
        "preferred_teaching_language": preferred_teaching_language,
        "coach_avatar_id": coach_avatar_id,
        "coach_palette_id": coach_palette_id,
        "active_flow": active_flow,
        "active_session_id": active_session_id,
        "placement_status": placement_status,
        "unlock_state": unlock_state,
        "evaluated_class_no": evaluated_class_no,
        "active_learning_class_no": active_learning_class_no,
        "status": status,
        "next_action": next_action,
        "next_action_url": next_action_url,
        "allowed_next_actions": allowed_next_actions,
        "learner_message": learner_message,
        "parent_message": parent_message,
        "blocked_reason": blocked_reason,
    }


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def _session_state(session: dict[str, Any] | None) -> dict[str, Any]:
    if not session:
        return {}
    state_json = session.get("state_json")
    return state_json if isinstance(state_json, dict) else {}


def _session_id(session: dict[str, Any]) -> str:
    return str(session["session_id"])


def _class_url(target_class_no: int) -> str:
    return f"/school/classes/{target_class_no}"


def _chapter_url(target_class_no: int, chapter_id: Any) -> str:
    if chapter_id:
        return f"{_class_url(target_class_no)}/chapters/{chapter_id}"
    return _class_url(target_class_no)


def _is_active_linked_session(session: dict[str, Any] | None) -> bool:
    if not session:
        return False
    state = _session_state(session)
    status = str(state.get("status") or session.get("status") or "")
    return status in ACTIVE_LINKED_SESSION_STATUSES


def _live_processing_request(
    session: dict[str, Any] | None,
    fallback: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    candidates = []
    if session and isinstance(session.get("processing_answer_request"), dict):
        candidates.append(session["processing_answer_request"])
    if isinstance(fallback, dict):
        candidates.append(fallback)
    return next(
        (
            request
            for request in candidates
            if request.get("status") == PROCESSING_ANSWER_STATUS
            and request.get("stale") is False
        ),
        None,
    )


def _awaiting_evaluation_state(
    *,
    profile_fields: dict[str, Any],
    display_name: str,
    flow: str,
    session: dict[str, Any],
    placement_status: str,
    unlock_state: str,
    evaluated_class_no: int | None,
    active_learning_class_no: int | None,
    next_action_url: str,
) -> dict[str, Any]:
    return _build_state(
        **profile_fields,
        active_flow=flow,
        active_session_id=_session_id(session),
        placement_status=placement_status,
        unlock_state=unlock_state,
        evaluated_class_no=evaluated_class_no,
        active_learning_class_no=active_learning_class_no,
        status="awaiting_evaluation",
        next_action=None,
        next_action_url=next_action_url,
        allowed_next_actions=[],
        learner_message=(
            f"{display_name}, your answer is still being checked. Stay in this {flow}."
        ),
        parent_message=(
            "The learner's latest answer is still being evaluated before the next activity."
        ),
        blocked_reason="answer_evaluation_in_progress",
    )


def _profile_fields_with_session_coach(
    profile_fields: dict[str, Any],
    session: dict[str, Any],
) -> dict[str, Any]:
    identity = school_coach_identity(_session_state(session))
    if not all(identity.values()):
        return profile_fields
    return {**profile_fields, **identity}


def _recoverable_state(
    *,
    profile_fields: dict[str, Any],
    display_name: str,
) -> dict[str, Any]:
    return _build_state(
        **profile_fields,
        active_flow="none",
        active_session_id=None,
        placement_status="not_started",
        unlock_state="locked",
        evaluated_class_no=None,
        active_learning_class_no=None,
        status="recoverable_error",
        next_action="retry",
        next_action_url=SCHOOL_HOME_URL,
        allowed_next_actions=["retry"],
        learner_message=(
            f"{display_name}, we could not restore your latest school step. Please retry."
        ),
        parent_message="The saved school state is inconsistent and needs to be loaded again.",
        blocked_reason="inconsistent_school_state",
    )


def _onboarding_state(*, profile_status: str) -> dict[str, Any]:
    return _build_state(
        profile_status=profile_status,
        target_class_no=None,
        subject_id=None,
        profile_version_id=None,
        preferred_teaching_language=None,
        coach_avatar_id=None,
        coach_palette_id=None,
        active_flow="onboarding",
        active_session_id=None,
        placement_status="not_started",
        unlock_state="locked",
        evaluated_class_no=None,
        active_learning_class_no=None,
        status="needs_action",
        next_action="complete_profile",
        next_action_url=SCHOOL_ONBOARDING_URL,
        allowed_next_actions=["complete_profile"],
        learner_message="Set up school prep before your readiness check.",
        parent_message=(
            "We need class, subject, and language details before testing readiness."
        ),
        blocked_reason=None,
    )


def _unsupported_catalog_state(
    *,
    profile_fields: dict[str, Any],
    display_name: str,
) -> dict[str, Any]:
    return _build_state(
        **profile_fields,
        active_flow="onboarding",
        active_session_id=None,
        placement_status="not_started",
        unlock_state="locked",
        evaluated_class_no=None,
        active_learning_class_no=None,
        status="needs_action",
        next_action="edit_profile",
        next_action_url=SCHOOL_ONBOARDING_URL,
        allowed_next_actions=["edit_profile"],
        learner_message=(
            f"{display_name}, choose an available board, subject, and class before "
            "starting the readiness check."
        ),
        parent_message=(
            "This saved curriculum selection is unavailable and must be updated."
        ),
        blocked_reason="unsupported_school_catalog_selection",
    )


def _insufficient_evidence_state(
    *,
    profile_fields: dict[str, Any],
    display_name: str,
    placement_session_id: str,
    evaluated_class_no: int | None,
) -> dict[str, Any]:
    return _build_state(
        **profile_fields,
        active_flow="placement",
        active_session_id=placement_session_id,
        placement_status="insufficient_evidence",
        unlock_state="locked",
        evaluated_class_no=evaluated_class_no,
        active_learning_class_no=None,
        status="insufficient_evidence",
        next_action="resume_placement",
        next_action_url=f"{SCHOOL_READINESS_URL}/{placement_session_id}",
        allowed_next_actions=["resume_placement"],
        learner_message=(
            f"{display_name}, finish the readiness check so there is enough evidence."
        ),
        parent_message=(
            "The readiness check needs more evidence before a learning path can be set."
        ),
        blocked_reason="insufficient_evidence",
    )


def school_state_for_profile(
    *,
    learner_profile: dict[str, Any],
    school_profile: dict[str, Any] | None,
    placement_session: dict[str, Any] | None = None,
    placement_report: dict[str, Any] | None = None,
    active_recap_session: dict[str, Any] | None = None,
    active_curriculum_session: dict[str, Any] | None = None,
    processing_answer_request: dict[str, Any] | None = None,
    active_masterclass_session: dict[str, Any] | None = None,
    active_support_session: dict[str, Any] | None = None,
    linked_session: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if school_profile is None:
        return _onboarding_state(profile_status="missing")

    subject_ids = school_profile.get("subject_ids")
    if (
        school_profile.get("target_class_no") is None
        or not school_profile.get("profile_version_id")
        or not subject_ids
        or not school_profile.get("preferred_teaching_language")
    ):
        return _onboarding_state(profile_status="incomplete")

    target_class_no = int(school_profile["target_class_no"])
    subject_id = str(subject_ids[0])
    display_name = (
        school_profile.get("display_name")
        or learner_profile.get("name")
        or learner_profile.get("display_name")
        or "learner"
    )
    profile_fields = {
        "profile_status": "complete",
        "target_class_no": target_class_no,
        "subject_id": subject_id,
        "profile_version_id": str(school_profile["profile_version_id"]),
        "preferred_teaching_language": str(
            school_profile["preferred_teaching_language"]
        ),
        **school_coach_identity(school_profile),
    }

    if not school_catalog_selection_available(school_profile):
        return _unsupported_catalog_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
        )

    if (active_recap_session or active_curriculum_session) and not placement_report:
        return _recoverable_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
        )

    report_status = (
        str(placement_report.get("placement_status") or "")
        if placement_report
        else "not_started"
    )
    report_unlock = (
        str(placement_report.get("unlock_state") or "")
        if placement_report
        else "locked"
    )
    evaluated_class_no = _optional_int(
        placement_report.get("evaluated_class_no") if placement_report else None
    )

    if placement_report and (report_status, report_unlock) not in VALID_REPORT_TRANSITIONS:
        return _recoverable_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
        )

    if active_curriculum_session and (
        report_status,
        report_unlock,
    ) != ("target_ready", "target_unlocked"):
        return _recoverable_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
        )

    recap_state = _session_state(active_recap_session)
    recap_status = str(
        recap_state.get("status") or (active_recap_session or {}).get("status") or ""
    )

    curriculum_state = _session_state(active_curriculum_session)
    levels_value = curriculum_state.get("levels")
    if active_curriculum_session and levels_value is not None and (
        not isinstance(levels_value, list)
        or any(not isinstance(level, dict) for level in levels_value)
    ):
        return _recoverable_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
        )
    chapter_value = curriculum_state.get("chapter")
    if (
        active_curriculum_session
        and chapter_value is not None
        and not isinstance(chapter_value, dict)
    ):
        return _recoverable_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
        )
    chapter = chapter_value or {}
    curriculum_url = (
        f"/school/session/{_session_id(active_curriculum_session)}"
        if active_curriculum_session
        else _chapter_url(target_class_no, chapter.get("chapter_id"))
    )
    if linked_session:
        linked_flow = str(linked_session.get("flow_type") or "")
        if (
            linked_flow == "masterclass"
            and not active_masterclass_session
            and _is_active_linked_session(linked_session)
        ):
            active_masterclass_session = linked_session
        elif (
            linked_flow == "support"
            and not active_support_session
            and _is_active_linked_session(linked_session)
        ):
            active_support_session = linked_session

    active_linked_session = (
        active_masterclass_session
        if _is_active_linked_session(active_masterclass_session)
        else active_support_session
        if _is_active_linked_session(active_support_session)
        else None
    )
    linked_processing = _live_processing_request(active_linked_session)
    if active_linked_session and linked_processing:
        linked_flow = str(active_linked_session.get("flow_type") or "")
        if linked_flow not in {"masterclass", "support"}:
            return _recoverable_state(
                profile_fields=profile_fields,
                display_name=str(display_name),
            )
        linked_session_id = _session_id(active_linked_session)
        return _awaiting_evaluation_state(
            profile_fields=_profile_fields_with_session_coach(
                profile_fields,
                active_linked_session,
            ),
            display_name=str(display_name),
            flow=linked_flow,
            session=active_linked_session,
            placement_status=report_status,
            unlock_state=report_unlock,
            evaluated_class_no=evaluated_class_no,
            active_learning_class_no=target_class_no,
            next_action_url=f"/school/{linked_flow}/{linked_session_id}",
        )

    curriculum_processing = _live_processing_request(
        active_curriculum_session,
        processing_answer_request,
    )
    if active_curriculum_session and curriculum_processing:
        return _awaiting_evaluation_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
            flow="curriculum",
            session=active_curriculum_session,
            placement_status=report_status,
            unlock_state=report_unlock,
            evaluated_class_no=evaluated_class_no,
            active_learning_class_no=target_class_no,
            next_action_url=curriculum_url,
        )

    recap_processing = _live_processing_request(active_recap_session)
    if active_recap_session and recap_processing:
        return _awaiting_evaluation_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
            flow="recap",
            session=active_recap_session,
            placement_status=report_status,
            unlock_state=report_unlock,
            evaluated_class_no=evaluated_class_no,
            active_learning_class_no=_optional_int(
                recap_state.get("active_learning_class_no")
            ),
            next_action_url=f"/school/recap/{_session_id(active_recap_session)}",
        )

    placement_processing = _live_processing_request(placement_session)
    if placement_session and placement_processing:
        return _awaiting_evaluation_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
            flow="placement",
            session=placement_session,
            placement_status="in_progress",
            unlock_state="locked",
            evaluated_class_no=None,
            active_learning_class_no=None,
            next_action_url=(
                f"{SCHOOL_READINESS_URL}/{_session_id(placement_session)}"
            ),
        )

    if active_linked_session:
        linked_flow = str(active_linked_session.get("flow_type") or "")
        if linked_flow not in {"masterclass", "support"}:
            return _recoverable_state(
                profile_fields=profile_fields,
                display_name=str(display_name),
            )
        linked_session_id = _session_id(active_linked_session)
        next_action = f"resume_{linked_flow}"
        return _build_state(
            **_profile_fields_with_session_coach(
                profile_fields,
                active_linked_session,
            ),
            active_flow=linked_flow,
            active_session_id=linked_session_id,
            placement_status=report_status,
            unlock_state=report_unlock,
            evaluated_class_no=evaluated_class_no,
            active_learning_class_no=target_class_no,
            status="in_progress",
            next_action=next_action,
            next_action_url=f"/school/{linked_flow}/{linked_session_id}",
            allowed_next_actions=[next_action],
            learner_message=(
                f"{display_name}, continue your focused {linked_flow} from where you left off."
            ),
            parent_message=(
                f"The learner is completing focused {linked_flow} support before continuing."
            ),
            blocked_reason=None,
        )

    if active_curriculum_session:
        curriculum_phase = str(curriculum_state.get("phase") or "")
        curriculum_status = str(
            curriculum_state.get("status")
            or active_curriculum_session.get("status")
            or ""
        )
        if (
            curriculum_status == "paused_for_masterclass"
            and curriculum_phase == "paused_for_masterclass"
            and isinstance(curriculum_state.get("active_interrupt"), dict)
        ):
            curriculum_session_id = _session_id(active_curriculum_session)
            return _build_state(
                **profile_fields,
                active_flow="masterclass",
                active_session_id=curriculum_session_id,
                placement_status=report_status,
                unlock_state=report_unlock,
                evaluated_class_no=evaluated_class_no,
                active_learning_class_no=target_class_no,
                status="needs_action",
                next_action="start_masterclass",
                next_action_url=curriculum_url,
                allowed_next_actions=["start_masterclass"],
                learner_message=(
                    f"{display_name}, start the focused coach session before returning "
                    "to this chapter."
                ),
                parent_message=(
                    "The learner needs one focused coach session before continuing."
                ),
                blocked_reason=None,
            )
        if curriculum_status == "complete" and curriculum_phase == "complete":
            next_available_chapter = curriculum_state.get(
                "next_available_chapter"
            )
            if next_available_chapter:
                return _build_state(
                    **profile_fields,
                    active_flow="curriculum",
                    active_session_id=_session_id(active_curriculum_session),
                    placement_status=report_status,
                    unlock_state="target_unlocked",
                    evaluated_class_no=evaluated_class_no,
                    active_learning_class_no=target_class_no,
                    status="complete",
                    next_action="start_curriculum",
                    next_action_url=_class_url(target_class_no),
                    allowed_next_actions=["start_curriculum"],
                    learner_message=(
                        f"{display_name}, this chapter is complete. Start the next chapter."
                    ),
                    parent_message=(
                        "The learner completed this chapter and can continue to the next one."
                    ),
                    blocked_reason=None,
                )
            return _build_state(
                **profile_fields,
                active_flow="curriculum",
                active_session_id=_session_id(active_curriculum_session),
                placement_status=report_status,
                unlock_state="target_unlocked",
                evaluated_class_no=evaluated_class_no,
                active_learning_class_no=target_class_no,
                status="complete",
                next_action="view_report",
                next_action_url="/school/reports",
                allowed_next_actions=["view_report"],
                learner_message=(
                    f"{display_name}, your available Class {target_class_no} "
                    f"{subject_id.title()} chapters are complete."
                ),
                parent_message=(
                    "The learner completed all currently available target-class chapters."
                ),
                blocked_reason=None,
            )
        if curriculum_phase in {"needs_support", "capped_support"}:
            support_required = curriculum_state.get("support_required")
            if not isinstance(support_required, dict):
                return _recoverable_state(
                    profile_fields=profile_fields,
                    display_name=str(display_name),
                )
            return _build_state(
                **profile_fields,
                active_flow="support",
                active_session_id=_session_id(active_curriculum_session),
                placement_status=report_status,
                unlock_state="target_unlocked",
                evaluated_class_no=evaluated_class_no,
                active_learning_class_no=target_class_no,
                status="needs_support",
                next_action="view_support_plan",
                next_action_url=(
                    f"/school/support/{_session_id(active_curriculum_session)}"
                ),
                allowed_next_actions=["view_support_plan"],
                learner_message=(
                    f"{display_name}, open your support plan before continuing this chapter."
                ),
                parent_message=(
                    "The learner needs focused support before this chapter can continue."
                ),
                blocked_reason=str(
                    support_required.get("reason") or "chapter_support_required"
                ),
            )
        if curriculum_status != "active" or curriculum_phase not in ACTIVE_CURRICULUM_PHASES:
            return _recoverable_state(
                profile_fields=profile_fields,
                display_name=str(display_name),
            )
        return _build_state(
            **profile_fields,
            active_flow="curriculum",
            active_session_id=_session_id(active_curriculum_session),
            placement_status=report_status,
            unlock_state="target_unlocked",
            evaluated_class_no=evaluated_class_no,
            active_learning_class_no=target_class_no,
            status="in_progress",
            next_action="resume_curriculum",
            next_action_url=curriculum_url,
            allowed_next_actions=["resume_curriculum"],
            learner_message=(
                f"{display_name}, continue Class {target_class_no} "
                f"{subject_id.title()}: {chapter.get('title') or 'your chapter'}."
            ),
            parent_message=(
                "The learner is now working inside the target-class teaching loop."
            ),
            blocked_reason=None,
        )

    if active_recap_session:
        recap_session_id = _session_id(active_recap_session)
        active_learning_class_no = _optional_int(
            recap_state.get("active_learning_class_no")
        )
        placement_status = report_status
        unlock_state = report_unlock

        if recap_status == "complete":
            return _build_state(
                **profile_fields,
                active_flow="curriculum",
                active_session_id=None,
                placement_status=placement_status,
                unlock_state="target_unlocked",
                evaluated_class_no=evaluated_class_no or active_learning_class_no,
                active_learning_class_no=target_class_no,
                status="complete",
                next_action="start_curriculum",
                next_action_url=_class_url(target_class_no),
                allowed_next_actions=["start_curriculum"],
                learner_message=(
                    f"{display_name}, your recap path is complete. Start your target class: "
                    f"Class {target_class_no} {subject_id.title()}."
                ),
                parent_message=(
                    "The learner completed the prerequisite recap path and can now start "
                    "target-class work."
                ),
                blocked_reason=None,
            )

        if recap_status in {"needs_support", "capped_support"}:
            support_required = recap_state.get("support_required")
            if not isinstance(support_required, dict):
                return _recoverable_state(
                    profile_fields=profile_fields,
                    display_name=str(display_name),
                )
            blocked_reason = (
                support_required.get("reason")
                if recap_status == "capped_support"
                else "recap_support_required"
            ) or "recap_support_required"
            return _build_state(
                **profile_fields,
                active_flow="support",
                active_session_id=recap_session_id,
                placement_status=placement_status,
                unlock_state=unlock_state,
                evaluated_class_no=evaluated_class_no,
                active_learning_class_no=active_learning_class_no,
                status="needs_support",
                next_action="view_support_plan",
                next_action_url=f"/school/support/{recap_session_id}",
                allowed_next_actions=["view_support_plan"],
                learner_message=(
                    f"{display_name}, open your support plan before continuing the recap path."
                ),
                parent_message=(
                    "The learner needs a revised support step before continuing class work."
                ),
                blocked_reason=str(blocked_reason),
            )

        if recap_status == "needs_path_revision":
            return _build_state(
                **profile_fields,
                active_flow="recap",
                active_session_id=recap_session_id,
                placement_status=placement_status,
                unlock_state=unlock_state,
                evaluated_class_no=evaluated_class_no,
                active_learning_class_no=active_learning_class_no,
                status="needs_path_revision",
                next_action="revise_recap_path",
                next_action_url=f"/school/recap/{recap_session_id}",
                allowed_next_actions=["revise_recap_path"],
                learner_message=(
                    f"{display_name}, your recap path needs an update before you continue."
                ),
                parent_message=(
                    "The learner's prerequisite path needs revision before class chapters."
                ),
                blocked_reason="recap_path_revision_required",
            )

        if recap_status == ACTIVE_LINKED_SESSION_STATUS:
            return _build_state(
                **profile_fields,
                active_flow="recap",
                active_session_id=recap_session_id,
                placement_status=placement_status,
                unlock_state=unlock_state,
                evaluated_class_no=evaluated_class_no,
                active_learning_class_no=active_learning_class_no,
                status="in_progress",
                next_action="resume_recap",
                next_action_url=f"/school/recap/{recap_session_id}",
                allowed_next_actions=["resume_recap"],
                learner_message=(
                    f"{display_name}, continue your recap path from where you left off."
                ),
                parent_message=(
                    "The learner is rebuilding prerequisite foundations before class chapters."
                ),
                blocked_reason=None,
            )

        return _recoverable_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
        )

    placement_session_status = (
        str(placement_session.get("status") or "") if placement_session else ""
    )
    if placement_session and (
        placement_session_status == "insufficient_evidence"
        or report_status == "insufficient_evidence"
    ):
        return _insufficient_evidence_state(
            profile_fields=profile_fields,
            display_name=str(display_name),
            placement_session_id=_session_id(placement_session),
            evaluated_class_no=evaluated_class_no,
        )

    if placement_session and placement_session_status in ACTIVE_PLACEMENT_STATUSES:
        placement_session_id = _session_id(placement_session)
        return _build_state(
            **profile_fields,
            active_flow="placement",
            active_session_id=placement_session_id,
            placement_status="in_progress",
            unlock_state="locked",
            evaluated_class_no=None,
            active_learning_class_no=None,
            status="in_progress",
            next_action="resume_placement",
            next_action_url=f"{SCHOOL_READINESS_URL}/{placement_session_id}",
            allowed_next_actions=["resume_placement"],
            learner_message=(
                f"{display_name}, continue the readiness check from where you left off."
            ),
            parent_message=(
                "The readiness check is still in progress. Target class is not unlocked yet."
            ),
            blocked_reason=None,
        )

    if placement_session and placement_report:
        if report_unlock == "target_unlocked":
            return _build_state(
                **profile_fields,
                active_flow="curriculum",
                active_session_id=None,
                placement_status=report_status,
                unlock_state="target_unlocked",
                evaluated_class_no=evaluated_class_no,
                active_learning_class_no=target_class_no,
                status="ready",
                next_action="start_curriculum",
                next_action_url=_class_url(target_class_no),
                allowed_next_actions=["start_curriculum"],
                learner_message=placement_report.get("learner_summary")
                or f"{display_name}, your target class is unlocked.",
                parent_message=placement_report.get("parent_summary")
                or "The learner is ready for target-class work.",
                blocked_reason=None,
            )
        if report_status == "abandoned":
            return _build_state(
                **profile_fields,
                active_flow="placement_report",
                active_session_id=_session_id(placement_session),
                placement_status="abandoned",
                unlock_state="locked",
                evaluated_class_no=evaluated_class_no,
                active_learning_class_no=None,
                status="recoverable_error",
                next_action="start_placement",
                next_action_url=SCHOOL_READINESS_URL,
                allowed_next_actions=["view_placement_report", "start_placement"],
                learner_message=(
                    f"{display_name}, your readiness check stopped before a path was unlocked."
                ),
                parent_message=(
                    "The readiness check was abandoned. Review the saved report before restarting."
                ),
                blocked_reason="placement_abandoned",
            )
        return _build_state(
            **profile_fields,
            active_flow="placement_report",
            active_session_id=_session_id(placement_session),
            placement_status=report_status,
            unlock_state=report_unlock,
            evaluated_class_no=evaluated_class_no,
            active_learning_class_no=_optional_int(
                placement_report.get("active_learning_class_no")
            ),
            status="ready",
            next_action="start_recap",
            next_action_url=SCHOOL_RECAP_URL,
            allowed_next_actions=["view_placement_report", "start_recap"],
            learner_message=placement_report.get("learner_summary")
            or f"{display_name}, your readiness report is ready.",
            parent_message=placement_report.get("parent_summary")
            or "The readiness report is ready.",
            blocked_reason=None,
        )

    if not placement_session:
        return _build_state(
            **profile_fields,
            active_flow="none",
            active_session_id=None,
            placement_status="not_started",
            unlock_state="locked",
            evaluated_class_no=None,
            active_learning_class_no=None,
            status="needs_action",
            next_action="start_placement",
            next_action_url=SCHOOL_READINESS_URL,
            allowed_next_actions=["start_placement"],
            learner_message=(
                f"{display_name}, start your readiness check when you are ready."
            ),
            parent_message="The next step is a readiness check, not a chapter lesson.",
            blocked_reason=None,
        )

    return _recoverable_state(
        profile_fields=profile_fields,
        display_name=str(display_name),
    )
