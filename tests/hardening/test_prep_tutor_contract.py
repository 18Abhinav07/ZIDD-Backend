import asyncio
import json
from datetime import datetime, timezone

from app.ai.schemas import CriterionEval, PrepRubricEval
from app.services import session_service as svc
from app.services.rubric_engine import apply_caps, build_evaluation_packet, compute_attempt_credit
from app.services.content_personalization import render_gd_bridge_exercise
from app.services.tutor_plan import build_tutor_turn_plan
from app.graph.nodes.bridge import personalize_bridge_exercise


def _run(coro):
    return asyncio.run(coro)


def test_missing_required_criterion_caps_score_and_blocks_pass():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I support AI in campus placements because it helps students get jobs faster."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="clear_stance", met=True, quality=0.8, evidence_quote="I support AI"),
            CriterionEval(
                id="concrete_evidence",
                met=False,
                quality=0.2,
                reason="No example, data, case, comparison, or concrete observation is provided.",
            ),
            CriterionEval(
                id="topic_relevance",
                met=True,
                quality=0.9,
                evidence_quote="AI in campus placements",
            ),
        ],
        required_missing=["concrete_evidence"],
        strengths=["clear stance"],
        errors=["missing evidence"],
        next_focus="Add one concrete example or data-backed reason.",
        on_task=True,
        english=True,
        affect="neutral",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.effective_score <= 0.62
    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert "concrete_evidence" in result.required_missing
    assert "missing_required:concrete_evidence" in result.blockers


def test_prep_rubric_schema_uses_plan_field_names_but_accepts_legacy_aliases():
    schema = PrepRubricEval.model_json_schema()

    assert "raw_score" in schema["properties"]
    assert "required_missing" in schema["properties"]
    assert "score" not in schema["properties"]
    criterion_props = schema["$defs"]["CriterionEval"]["properties"]
    assert "id" in criterion_props
    assert "quality" in criterion_props
    assert "criterion_id" not in criterion_props

    parsed = PrepRubricEval.model_validate(
        {
            "score": 0.72,
            "missing_required_criteria": ["concrete_evidence"],
            "criteria": [
                {
                    "criterion_id": "clear_stance",
                    "met": True,
                    "score": 0.7,
                    "rationale": "Stance is present.",
                    "evidence_quote": "AI is useful",
                }
            ],
            "next_focus": "Add evidence.",
        }
    )

    assert parsed.raw_score == 0.72
    assert parsed.required_missing == ["concrete_evidence"]
    assert parsed.criteria[0].id == "clear_stance"
    assert parsed.criteria[0].quality == 0.7
    assert parsed.criteria[0].reason == "Stance is present."


def test_required_criterion_marked_met_without_quote_is_not_valid_proof():
    state = svc._new_state("user-1", "session-1", "int_06_own_a_failure", [], task_type="interview_prep")
    answer = "I made a migration mistake and I learned to test more carefully."
    packet = build_evaluation_packet(state, svc.get_node("int_06_own_a_failure"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.86,
        criteria=[
            CriterionEval(id="ownership", met=True, quality=0.8, evidence_quote="I made a migration mistake"),
            CriterionEval(id="impact", met=True, quality=0.7, evidence_quote="migration mistake"),
            CriterionEval(id="response_action", met=True, quality=0.8, evidence_quote=""),
            CriterionEval(id="prevention", met=True, quality=0.8, evidence_quote="test more carefully"),
        ],
        required_missing=[],
        strengths=["owns the mistake"],
        errors=[],
        next_focus="Add the immediate response action.",
        on_task=True,
        english=True,
        affect="neutral",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert "response_action" in result.required_missing
    assert "invalid_proof:response_action" in result.blockers


def test_tutor_plan_for_partial_answer_disallows_mastery_praise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "I think AI is useful because it helps.",
    )
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.72,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.7, evidence_quote="AI is useful"),
                CriterionEval(id="concrete_evidence", met=False, quality=0.1),
                CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="AI"),
            ],
            required_missing=["concrete_evidence"],
            strengths=["clear stance"],
            errors=["missing evidence"],
            next_focus="Add one concrete example.",
            on_task=True,
            english=True,
            affect="neutral",
            pass_eligible=True,
            mastery_eligible=False,
        ),
    )

    plan = build_tutor_turn_plan(result, state)

    assert plan.verdict == "partial"
    assert plan.next_action == "rewrite"
    assert plan.allowed_praise is False
    assert plan.tone_policy == "direct_no_praise"
    assert plan.focus == "Add one concrete example."


def test_completed_but_not_mastered_progress_does_not_display_done_or_100(store):
    _run(store.ensure_profile("user-1"))
    _run(
        store.upsert_mastery(
            "user-1",
            "gd_02_support_with_evidence",
            0.43,
            5,
            clean_pass=True,
            node_completed=True,
            node_mastered=False,
            display_status="ready_to_advance",
            independent_passes=2,
            last_gap="Needs one concrete evidence-backed transfer answer.",
        )
    )

    rows = _run(svc.get_progression_map("user-1", "group_discussion"))
    node = next(row for row in rows if row["node_id"] == "gd_02_support_with_evidence")

    assert node["completed"] is True
    assert node["mastered"] is False
    assert node["status"] == "ready_to_advance"
    assert node["display_status"] == "ready_to_advance"
    assert node["display_mastery"] == 0.43
    assert node["last_gap"] == "Needs one concrete evidence-backed transfer answer."


def test_legacy_school_completed_rows_still_render_mastered(store):
    _run(store.ensure_profile("user-1"))
    _run(
        store.upsert_mastery(
            "user-1",
            "comm_00_greetings",
            0.0,
            2,
            clean_pass=False,
            node_completed=True,
            node_mastered=False,
            display_status="active",
        )
    )

    rows = _run(svc.get_progression_map("user-1", "communication"))
    node = next(row for row in rows if row["node_id"] == "comm_00_greetings")

    assert node["completed"] is True
    assert node["mastered"] is True
    assert node["status"] == "mastered"
    assert node["display_mastery"] == 1.0


def test_legacy_career_completed_rows_render_ready_not_mastered(store):
    _run(store.ensure_profile("user-1"))
    _run(
        store.upsert_mastery(
            "user-1",
            "int_01_elevator_pitch",
            0.0,
            2,
            clean_pass=False,
            node_completed=True,
            node_mastered=False,
            display_status="active",
        )
    )

    rows = _run(svc.get_progression_map("user-1", "interview"))
    node = next(row for row in rows if row["node_id"] == "int_01_elevator_pitch")

    assert node["completed"] is True
    assert node["mastered"] is False
    assert node["status"] == "ready_to_advance"
    assert node["display_mastery"] == 0.0


def test_two_good_independent_attempts_cannot_mark_ready_or_mastered():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I support AI in campus placements because a pilot can compare interview time and shortlist accuracy before full rollout."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.88,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.85, evidence_quote="I support AI"),
                CriterionEval(id="concrete_evidence", met=True, quality=0.85, evidence_quote="a pilot can compare interview time and shortlist accuracy"),
                CriterionEval(id="topic_relevance", met=True, quality=0.9, evidence_quote="AI in campus placements"),
            ],
            strengths=["clear stance with concrete evidence"],
            errors=[],
            next_focus="Prove this under pressure.",
            on_task=True,
            english=True,
            affect="neutral",
            pass_eligible=True,
            mastery_eligible=True,
        ),
    )

    progress = {}
    for _ in range(2):
        progress = compute_attempt_credit(progress, result)

    assert progress["independent_passes"] == 2
    assert progress["meaningful_attempts"] == 2
    assert progress["display_status"] == "in_progress"
    assert progress["node_mastered"] is False


def test_five_independent_attempts_are_not_ready_without_transfer_or_pressure():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I support AI in campus placements because a pilot can compare interview time and shortlist accuracy before full rollout."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.88,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.85, evidence_quote="I support AI"),
                CriterionEval(id="concrete_evidence", met=True, quality=0.85, evidence_quote="a pilot can compare interview time and shortlist accuracy"),
                CriterionEval(id="topic_relevance", met=True, quality=0.9, evidence_quote="AI in campus placements"),
            ],
            strengths=["clear stance with concrete evidence"],
            errors=[],
            next_focus="Try a transfer example.",
            on_task=True,
            english=True,
            affect="neutral",
            pass_eligible=True,
            mastery_eligible=True,
        ),
    )

    progress = {}
    for _ in range(5):
        progress = compute_attempt_credit(progress, result)

    assert progress["display_status"] == "in_progress"
    assert progress["node_mastered"] is False


def test_track_turn_records_enforced_rubric_ledger(store):
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = "I think AI is useful because it helps."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.72,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.7, evidence_quote="AI is useful"),
                CriterionEval(id="concrete_evidence", met=False, quality=0.1),
                CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="AI"),
            ],
            required_missing=["concrete_evidence"],
            strengths=["clear stance"],
            errors=["missing evidence"],
            next_focus="Add one concrete example.",
            on_task=True,
            english=True,
            affect="neutral",
            pass_eligible=True,
            mastery_eligible=False,
        ),
    )
    plan = build_tutor_turn_plan(result, state)
    state.update(
        {
            "user_input": answer,
            "last_diagnosis": {
                "on_task": True,
                "english": True,
                "affect": "neutral",
                "next_focus": result.next_focus,
            },
            "last_eval_score": result.effective_score,
            "last_rubric_result": result.model_dump(),
            "tutor_turn_plan": plan.model_dump(),
            "active_turn_id": "turn-1",
            "attempts": 3,
        }
    )

    _run(svc._track_turn(state, "gd_02_support_with_evidence"))

    assert len(store.turn_evaluations) == 1
    row = store.turn_evaluations[0]
    assert row["evaluation_id"] == "session-1:turn-1:gd_02_support_with_evidence"
    assert row["effective_score"] <= 0.62
    assert row["pass_eligible"] is False
    assert row["blockers"] == ["missing_required:concrete_evidence"]


def test_prep_bridge_fill_records_scaffold_credit_and_not_independent_pass(store):
    from app.graph.nodes import evaluate as eval_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    state["pending_answer_key"] = {"type": "fill_blank", "answer_key": "for example"}
    state["user_input"] = "for example"
    state["active_turn_id"] = "turn-bridge"

    updates = _run(eval_node.evaluate_node(state))
    state.update(updates)
    svc._update_progress(state)
    _run(svc._track_turn(state, "gd_02_support_with_evidence"))

    assert state["scaffold_successes"] == 1
    assert state["independent_passes"] == 0
    assert state["node_mastered"] is False
    assert state["clean_streak"] == 0
    assert state["last_rubric_result"]["attempt_type"] == "scaffolded"
    assert len(store.turn_evaluations) == 1
    assert store.turn_evaluations[0]["attempt_type"] == "scaffolded"


def test_open_bridge_prompt_marker_classifies_next_answer_as_scaffolded():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Remote work policy"]},
    )
    state["active_prompt_attempt_type"] = "scaffolded"
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "Remote work helps because it saves commute time.",
    )

    assert packet.attempt_type == "scaffolded"

    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.9,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.9, evidence_quote="Remote work helps"),
                CriterionEval(id="concrete_evidence", met=True, quality=0.9, evidence_quote="saves commute time"),
                CriterionEval(id="topic_relevance", met=True, quality=0.9, evidence_quote="Remote work"),
            ],
            strengths=["clear answer"],
            errors=[],
            next_focus="Try the same move without a scaffold.",
            pass_eligible=True,
            mastery_eligible=True,
        ),
    )
    progress = compute_attempt_credit({}, result)

    assert progress["scaffold_successes"] == 1
    assert progress["independent_passes"] == 0
    assert progress["node_mastered"] is False


def test_stale_last_graded_bridge_does_not_classify_next_open_answer_as_scaffolded():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Remote work policy"]},
    )
    state["last_graded_bridge"] = True
    state["active_prompt_attempt_type"] = None
    state["pending_answer_key"] = None
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "Remote work helps because it saves commute time.",
    )

    assert packet.attempt_type == "independent"


def test_langgraph_preserves_prep_rubric_result_channel(monkeypatch):
    from app.graph import build as graph_build
    from app.graph.nodes import evaluate as eval_node

    async def fake_prep_eval(node, messages, user_input, **kwargs):
        packet = build_evaluation_packet(kwargs["state"], node, user_input)
        return apply_caps(
            packet,
            PrepRubricEval(
                raw_score=0.9,
                criteria=[
                        CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
                        CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI"),
                        CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer using FastAPI"),
                    ],
                strengths=["specific backend detail"],
                errors=[],
                next_focus="Try a pressure version.",
                pass_eligible=True,
                mastery_eligible=True,
            ),
        )

    monkeypatch.setattr(eval_node, "evaluate_prep_answer", fake_prep_eval)
    graph_build.get_graph.cache_clear()
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [{"role": "assistant", "content": "opening"}],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["turn_count"] = 1
    state["user_input"] = "I am a backend engineer using FastAPI."

    try:
        updates = _run(graph_build.get_graph().ainvoke(state))
    finally:
        graph_build.get_graph.cache_clear()

    assert updates["last_rubric_result"]["pass_eligible"] is True
    assert updates["tutor_turn_plan"]["verdict"] in {"independent_pass", "partial"}
    assert updates["last_diagnosis"]["score"] == updates["last_rubric_result"]["effective_score"]


def test_prep_eval_exception_fails_closed_with_rubric_result(monkeypatch):
    from app.graph import build as graph_build
    from app.graph.nodes import evaluate as eval_node

    async def broken_prep_eval(*_args, **_kwargs):
        raise RuntimeError("structured model unavailable")

    monkeypatch.setattr(eval_node, "evaluate_prep_answer", broken_prep_eval)
    graph_build.get_graph.cache_clear()
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [{"role": "assistant", "content": "opening"}],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["turn_count"] = 1
    state["user_input"] = "I am a backend engineer using FastAPI."

    try:
        updates = _run(graph_build.get_graph().ainvoke(state))
    finally:
        graph_build.get_graph.cache_clear()

    rubric = updates["last_rubric_result"]
    assert rubric["pass_eligible"] is False
    assert rubric["mastery_eligible"] is False
    assert "structured_eval_unavailable" in rubric["blockers"]
    assert "answers_question" in rubric["required_missing"]
    assert updates["tutor_turn_plan"]["allowed_praise"] is False


def test_evaluation_packet_recent_messages_are_json_serializable():
    packet = build_evaluation_packet(
        {
            "messages": [
                {
                    "role": "assistant",
                    "content": "opening",
                    "created_at": datetime.now(timezone.utc),
                    "message_kind": "opening",
                },
                {
                    "role": "user",
                    "content": "I build FastAPI systems.",
                    "created_at": datetime.now(timezone.utc),
                    "message_kind": "learner_answer",
                },
            ],
            "career_context": {"primary_role": "Backend Software Engineer"},
        },
        svc.get_node("int_01_elevator_pitch"),
        "I build FastAPI systems.",
    )

    dumped = packet.model_dump()
    assert "created_at" not in dumped["recent_messages"][0]
    assert dumped["recent_messages"][1]["message_kind"] == "learner_answer"
    json.dumps(dumped)


def test_interview_bridge_role_personalization_does_not_duplicate_backend_label():
    node = svc.get_node("int_01_elevator_pitch")
    exercise = next(item for item in node.bridge_exercises if item.id == "int_01_elevator_pitch_bx2")

    personalized = personalize_bridge_exercise(
        exercise,
        {
            "primary_role": "Backend Software Engineer",
            "target_roles": ["Backend Software Engineer", "Platform Engineer"],
            "role_family": "software_technical",
        },
        "interview",
    )

    joined = " ".join([personalized.sentence, *(personalized.options or [])])
    assert "Backend Backend Software Engineer" not in joined
    assert "Backend Software Engineer" in joined


def test_career_prep_without_rubric_result_fails_closed_no_legacy_advance():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["last_diagnosis"] = {"english": True, "on_task": True}
    state["last_clean_pass_score"] = 0.95
    state["last_eval_score"] = 0.95
    state["last_rubric_result"] = None

    for _ in range(3):
        svc._update_progress(state)

    assert state["clean_streak"] == 0
    assert state["display_status"] == "active"
    assert state["node_mastered"] is False


def test_prep_minimum_gate_caps_rubric_result_for_weak_gd_answer(monkeypatch):
    from app.graph.nodes import evaluate as eval_node

    async def overly_generous_eval(*_args, **_kwargs):
        return apply_caps(
            build_evaluation_packet(
                _args[-1] if _args and isinstance(_args[-1], dict) else {},
                svc.get_node("gd_02_support_with_evidence"),
                "I support this. It is good.",
            ),
            PrepRubricEval(
                raw_score=0.9,
                criteria=[
                    CriterionEval(id="clear_stance", met=True, quality=0.8, evidence_quote="I support this"),
                    CriterionEval(id="concrete_evidence", met=True, quality=0.8, evidence_quote="It is good"),
                    CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="this"),
                ],
                strengths=["clear stance"],
                errors=[],
                next_focus="Try a stronger example.",
                on_task=True,
                english=True,
                pass_eligible=True,
                mastery_eligible=True,
            ),
        )

    monkeypatch.setattr(eval_node, "evaluate_prep_answer", overly_generous_eval)
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    state["user_input"] = "I support this. It is good."

    updates = _run(eval_node.evaluate_node(state))

    assert updates["last_eval_score"] == 0.6
    assert updates["last_rubric_result"]["effective_score"] == 0.6
    assert updates["last_rubric_result"]["pass_eligible"] is False
    assert "minimum_gate_cap" in updates["last_rubric_result"]["blockers"]


def test_gd_bridge_rendering_uses_active_topic_without_stock_topic_residue():
    stock_terms = [
        "remote work",
        "bike lanes",
        "single-use plastics",
        "social media",
        "electric cars",
        "homework",
        "four-day work week",
        "minimum wage",
    ]
    context = {"gd_topics": ["AI in campus placements"]}
    for node_id in [
        "gd_01_stake_position",
        "gd_02_support_with_evidence",
        "gd_03_take_the_floor",
        "gd_04_build_on_others",
        "gd_05_disagree_respectfully",
        "gd_06_balanced_view",
        "gd_07_steer_back",
        "gd_08_include_quiet",
        "gd_09_manage_dominator",
        "gd_10_drive_consensus",
    ]:
        node = svc.get_node(node_id)
        rendered = [
            render_gd_bridge_exercise(exercise, node_id, context)
            for exercise in node.bridge_exercises
        ]
        parts = []
        for item in rendered:
            parts.extend([item.sentence, item.context, item.answer_key, " ".join(item.options or [])])
        combined = " ".join(parts).lower()

        assert "ai in campus placements" in combined
        for term in stock_terms:
            assert term not in combined


def test_gd_bridge_rendering_uses_generic_context_for_non_campus_topics():
    context = {"gd_topics": ["Should remote work be the default?"]}
    node = svc.get_node("gd_02_support_with_evidence")
    rendered = [
        render_gd_bridge_exercise(exercise, "gd_02_support_with_evidence", context)
        for exercise in node.bridge_exercises
    ]
    parts = []
    for item in rendered:
        parts.extend([item.sentence, item.context, item.answer_key, " ".join(item.options or [])])
    combined = " ".join(parts).lower()

    assert "remote work being the default" in combined
    for residue in ["college", "campus", "placement", "student", "weaker students"]:
        assert residue not in combined


def test_gd_topic_phrase_handles_auxiliary_should_motions():
    from app.graph.nodes.bridge import _gd_topic_phrase as bridge_topic_phrase
    from app.services.session_service import _gd_topic_phrase_for_state

    context = {"gd_topics": ["Should remote work be the default?"]}
    node = svc.get_node("gd_02_support_with_evidence")
    rendered = [
        render_gd_bridge_exercise(exercise, "gd_02_support_with_evidence", context)
        for exercise in node.bridge_exercises
    ]
    parts = []
    for item in rendered:
        parts.extend([item.sentence, item.answer_key, " ".join(item.options or [])])
    combined = " ".join(parts).lower()

    assert "remote work being the default" in combined

    context = {"gd_topics": ["Should companies be allowed to use AI in hiring?"]}
    rendered = [
        render_gd_bridge_exercise(exercise, "gd_02_support_with_evidence", context)
        for exercise in node.bridge_exercises
    ]
    parts = []
    for item in rendered:
        parts.extend([item.sentence, item.answer_key, " ".join(item.options or [])])
    combined = " ".join(parts).lower()

    assert "companies being allowed to use ai in hiring" in combined
    assert bridge_topic_phrase("Should remote work be the default?") == "remote work being the default"
    assert bridge_topic_phrase("Should companies be allowed to use AI in hiring?") == "companies being allowed to use AI in hiring"
    assert _gd_topic_phrase_for_state({"competency_node": "gd_02_support_with_evidence", "career_context": context}) == "companies being allowed to use AI in hiring"
