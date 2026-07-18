import json

from app.services.school_rebuild_growth_report import build_school_growth_report


CURRENT_SCOPE = {
    "session_id": "curriculum-session-current",
    "chapter_id": "eng_c5_ch02",
}
CURRENT_SESSION = {
    "session_id": CURRENT_SCOPE["session_id"],
    "api_version": "rebuild",
    "flow_type": "curriculum",
    "state_json": {"chapter": {"chapter_id": CURRENT_SCOPE["chapter_id"]}},
}
HISTORICAL_SESSION = {
    "session_id": "curriculum-session-historical",
    "api_version": "rebuild",
    "flow_type": "curriculum",
    "state_json": {"chapter": {"chapter_id": "eng_c5_ch01"}},
}


def _event(
    *,
    event_id: str,
    session_id: str,
    chapter_id: str,
    activity_id: str,
    skill_id: str = "reading.inference_reason",
    domain: str = "school",
    excerpt: str = "The clue shows why the character made that choice.",
    focus: str = "explain an inference with a clue",
    occurred_at: str = "2026-07-18T10:00:00+00:00",
    task_type: str = "school_rebuild_curriculum",
) -> dict:
    return {
        "source_event_key": event_id,
        "domain": domain,
        "task_type": task_type,
        "session_id": session_id,
        "node_id": activity_id,
        "skill_id": skill_id,
        "occurred_at": occurred_at,
        "evidence_json": {
            "chapter_id": chapter_id,
            "activity_id": activity_id,
            "skill_ids": [skill_id],
            "focus": focus,
            "learner_response_excerpt": excerpt,
        },
    }


def test_historical_transfer_with_same_skill_never_becomes_current_chapter_claim():
    historical_event = _event(
        event_id="event-historical-transfer",
        session_id="curriculum-session-historical",
        chapter_id="eng_c5_ch01",
        activity_id="transfer-activity",
    )
    report = build_school_growth_report(
        learning_events=[historical_event],
        school_profiles=[
            {
                "domain": "school",
                "skill_id": "reading.inference_reason",
                "evidence_json": {
                    "chapter_id": "eng_c5_ch01",
                    "level_id": "Try It Yourself",
                    "latest_quote": "Old transfer evidence only.",
                },
            }
        ],
        school_sessions=[CURRENT_SESSION, HISTORICAL_SESSION],
        current_scope=CURRENT_SCOPE,
        audience="learner",
    )

    assert report["status"] == "insufficient_evidence"
    assert report["current_chapter_claims"] == []
    assert len(report["historical_context"]) == 1
    historical_claim = report["historical_context"][0]
    assert historical_claim["scope"] == "historical_context"
    assert historical_claim["source_event_ids"] == ["event-historical-transfer"]
    assert historical_claim["session_id"] == "curriculum-session-historical"
    assert historical_claim["chapter_id"] == "eng_c5_ch01"
    assert historical_claim["skill_ids"] == ["reading.inference_reason"]
    assert "Try It Yourself" not in json.dumps(report)


def test_empty_or_unprovenanced_current_evidence_is_insufficient():
    unprovenanced_event = _event(
        event_id="event-missing-timestamp",
        session_id=CURRENT_SCOPE["session_id"],
        chapter_id=CURRENT_SCOPE["chapter_id"],
        activity_id="inference-activity",
    )
    del unprovenanced_event["occurred_at"]
    report = build_school_growth_report(
        learning_events=[unprovenanced_event],
        school_profiles=[
            {
                "domain": "school",
                "skill_id": "reading.inference_reason",
                "evidence_json": {
                    "latest_quote": "A profile projection is not event evidence.",
                },
            }
        ],
        school_sessions=[CURRENT_SESSION],
        current_scope=CURRENT_SCOPE,
        audience="parent",
    )

    assert report["status"] == "insufficient_evidence"
    assert report["insufficient_evidence"] == {
        "reason": "no_current_chapter_evidence"
    }
    assert report["current_chapter_claims"] == []
    assert report["historical_context"] == []


def test_matching_scope_event_renders_safe_derived_evidence_only():
    report = build_school_growth_report(
        learning_events=[
            _event(
                event_id="event-current",
                session_id=CURRENT_SCOPE["session_id"],
                chapter_id=CURRENT_SCOPE["chapter_id"],
                activity_id="inference-activity",
            )
        ],
        school_profiles=[],
        school_sessions=[CURRENT_SESSION],
        current_scope=CURRENT_SCOPE,
        audience="parent",
    )

    assert report["status"] == "ready"
    assert report["insufficient_evidence"] is None
    assert report["historical_context"] == []
    assert report["current_chapter_claims"] == [
        {
            "scope": "current_chapter",
            "message": (
                "Current chapter evidence records one learning activity."
            ),
            "source_event_ids": ["event-current"],
            "session_id": CURRENT_SCOPE["session_id"],
            "chapter_id": CURRENT_SCOPE["chapter_id"],
            "activity_id": "inference-activity",
            "skill_ids": ["reading.inference_reason"],
            "occurred_at": "2026-07-18T10:00:00+00:00",
            "evidence_label": "recorded_learning_activity",
            "evidence_count": 1,
        }
    ]


def test_non_school_rows_cannot_leak_into_the_report():
    report = build_school_growth_report(
        learning_events=[
            _event(
                event_id="event-school",
                session_id=CURRENT_SCOPE["session_id"],
                chapter_id=CURRENT_SCOPE["chapter_id"],
                activity_id="school-activity",
            ),
            _event(
                event_id="event-career",
                session_id=CURRENT_SCOPE["session_id"],
                chapter_id=CURRENT_SCOPE["chapter_id"],
                activity_id="career-activity",
                domain="career",
                excerpt="Career-only evidence must never appear.",
                focus="career-only focus",
            ),
        ],
        school_profiles=[
            {"domain": "school", "skill_id": "reading.inference_reason"},
            {
                "domain": "career",
                "skill_id": "interview.storytelling",
                "evidence_json": {"latest_quote": "Career profile evidence."},
            },
        ],
        school_sessions=[
            CURRENT_SESSION,
            {"session_id": "career-session", "domain": "career"},
        ],
        current_scope=CURRENT_SCOPE,
        audience="learner",
    )

    rendered = json.dumps(report)
    assert [
        claim["source_event_ids"] for claim in report["current_chapter_claims"]
    ] == [["event-school"]]
    assert "event-career" not in rendered
    assert "Career-only evidence" not in rendered
    assert "interview.storytelling" not in rendered


def test_report_never_renders_answer_model_or_rubric_evidence_text():
    event = _event(
        event_id="event-sensitive-evidence",
        session_id=CURRENT_SCOPE["session_id"],
        chapter_id=CURRENT_SCOPE["chapter_id"],
        activity_id="sensitive-activity",
        excerpt="Learner answer that must not render.",
        focus="Untrusted focus that must not render.",
    )
    event["evidence_json"]["model_answer"] = "Model answer that must not render."
    event["criteria_json"] = [
        {"evidence_quote": "Rubric quote that must not render."}
    ]

    report = build_school_growth_report(
        learning_events=[event],
        school_profiles=[],
        school_sessions=[CURRENT_SESSION],
        current_scope=CURRENT_SCOPE,
        audience="learner",
    )

    rendered = json.dumps(report)
    assert "Learner answer that must not render." not in rendered
    assert "Model answer that must not render." not in rendered
    assert "Rubric quote that must not render." not in rendered
    assert "Untrusted focus that must not render." not in rendered
    claim = report["current_chapter_claims"][0]
    assert claim["evidence_label"] == "recorded_learning_activity"
    assert claim["evidence_count"] == 1
    assert "learner_safe_evidence_excerpt" not in claim


def test_canonical_session_chapter_overrides_caller_and_event_chapter_mismatches():
    canonical_event = _event(
        event_id="event-canonical-chapter",
        session_id=CURRENT_SCOPE["session_id"],
        chapter_id=CURRENT_SCOPE["chapter_id"],
        activity_id="canonical-activity",
    )
    mismatched_event = _event(
        event_id="event-mismatched-chapter",
        session_id=CURRENT_SCOPE["session_id"],
        chapter_id="eng_c5_ch99",
        activity_id="mismatched-activity",
    )
    report = build_school_growth_report(
        learning_events=[canonical_event, mismatched_event],
        school_profiles=[],
        school_sessions=[CURRENT_SESSION],
        current_scope={
            "session_id": CURRENT_SCOPE["session_id"],
            "chapter_id": "caller-controlled-chapter",
        },
        audience="parent",
    )

    assert report["current_scope"] == CURRENT_SCOPE
    assert [
        claim["source_event_ids"] for claim in report["current_chapter_claims"]
    ] == [["event-canonical-chapter"]]
    assert [
        claim["source_event_ids"] for claim in report["historical_context"]
    ] == [["event-mismatched-chapter"]]


def test_untagged_or_non_rebuild_school_data_is_rejected():
    untagged_event = _event(
        event_id="event-untagged",
        session_id=CURRENT_SCOPE["session_id"],
        chapter_id=CURRENT_SCOPE["chapter_id"],
        activity_id="untagged-activity",
    )
    del untagged_event["task_type"]
    career_event = _event(
        event_id="event-career-rebuild-shaped",
        session_id=CURRENT_SCOPE["session_id"],
        chapter_id=CURRENT_SCOPE["chapter_id"],
        activity_id="career-activity",
        domain="career",
    )
    fabricated_rebuild_event = _event(
        event_id="event-fabricated-rebuild-type",
        session_id=CURRENT_SCOPE["session_id"],
        chapter_id=CURRENT_SCOPE["chapter_id"],
        activity_id="fabricated-activity",
        task_type="school_rebuild_unrecognized",
    )

    report = build_school_growth_report(
        learning_events=[untagged_event, career_event, fabricated_rebuild_event],
        school_profiles=[],
        school_sessions=[CURRENT_SESSION],
        current_scope=CURRENT_SCOPE,
        audience="learner",
    )

    assert report["status"] == "insufficient_evidence"
    assert report["current_chapter_claims"] == []
    assert report["historical_context"] == []

    legacy_session = {
        **CURRENT_SESSION,
        "api_version": "legacy",
    }
    legacy_report = build_school_growth_report(
        learning_events=[
            _event(
                event_id="event-legacy-session",
                session_id=CURRENT_SCOPE["session_id"],
                chapter_id=CURRENT_SCOPE["chapter_id"],
                activity_id="legacy-activity",
            )
        ],
        school_profiles=[],
        school_sessions=[legacy_session],
        current_scope=CURRENT_SCOPE,
        audience="learner",
    )
    assert legacy_report["insufficient_evidence"] == {
        "reason": "invalid_current_scope"
    }


def test_one_multi_skill_event_creates_one_event_counted_claim():
    event = _event(
        event_id="event-multi-skill",
        session_id=CURRENT_SCOPE["session_id"],
        chapter_id=CURRENT_SCOPE["chapter_id"],
        activity_id="multi-skill-activity",
        skill_id="reading.inference_reason",
    )
    event["evidence_json"]["skill_ids"] = [
        "reading.inference_reason",
        "reading.text_evidence",
    ]

    report = build_school_growth_report(
        learning_events=[event],
        school_profiles=[],
        school_sessions=[CURRENT_SESSION],
        current_scope=CURRENT_SCOPE,
        audience="learner",
    )

    claims = report["current_chapter_claims"]
    assert len(claims) == 1
    assert claims[0]["skill_ids"] == [
        "reading.inference_reason",
        "reading.text_evidence",
    ]
    assert claims[0]["evidence_count"] == 1
    assert sum(claim["evidence_count"] for claim in claims) == 1
