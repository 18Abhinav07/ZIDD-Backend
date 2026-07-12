import dataclasses

import pytest

from app.ai.schemas import CriterionEval, PrepRubricEval
from app.services import session_service as svc
from app.services.rubric_engine import apply_caps, assess_gd_evidence, build_evaluation_packet


def _all_met_eval(packet, answer: str) -> PrepRubricEval:
    return PrepRubricEval(
        raw_score=0.9,
        effective_score=0.9,
        next_focus="pressure test the same skill",
        criteria=[
            CriterionEval(
                id=str(criterion["id"]),
                met=True,
                evidence_quote=answer,
                reason="model marked the criterion met",
                quality=0.9,
            )
            for criterion in packet.criteria
        ],
        pass_eligible=True,
        mastery_eligible=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("module_id", ["interview", "group_discussion"])
async def test_career_placement_selects_without_persisting_completion(module_id, store):
    result = await svc.place_user(
        module_id,
        self_report="fluent",
        user_id="career-placement-user",
    )

    assert result["starting_node"]
    assert store.mastery == {}


def test_career_task_contract_is_frozen_and_serializes_safe_copies():
    from app.services.career_task_contract import CareerTaskContract

    contract = CareerTaskContract(
        prompt_id="prompt-7",
        context_id="ctx-7",
        active_role="Product Manager",
        active_topic="Remote work",
        semantic_anchors=("distributed teams", "delivery"),
        participant_claims=({"participant_id": "maya", "claim": "remote work widens access"},),
        evidence_policy="learner_owned_or_sourced",
        hypothetical=True,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        contract.prompt_id = "changed"
    with pytest.raises(TypeError):
        contract.participant_claims[0]["claim"] = "changed"
    dumped = contract.model_dump()
    dumped["participant_claims"][0]["claim"] = "changed"

    assert contract.participant_claims[0]["claim"] == "remote work widens access"
    assert CareerTaskContract.from_state({"active_task_contract": contract.model_dump()}) == contract
    assert CareerTaskContract.from_state({"active_task_contract": "bad-state"}) is None


def test_evaluation_packet_uses_exact_active_task_contract():
    contract = {
        "prompt_id": "prompt-transfer-2",
        "context_id": "ctx-new-market",
        "active_role": "Operations Manager",
        "active_topic": "Digital payments",
        "semantic_anchors": ["merchant adoption", "failed payments"],
        "participant_claims": [
            {"participant_id": "dev", "claim": "cash is more reliable", "stance": "oppose"}
        ],
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": False,
    }
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        module_id="group_discussion",
    )
    state["active_task_contract"] = contract

    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "I would test failed-payment rates before rollout.",
    )

    assert packet.active_role == "Operations Manager"
    assert packet.task_contract == contract


def test_visible_career_task_replaces_contract_only_when_committed():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
        career_context={"primary_role": "Data Analyst"},
    )
    first = {
        "message_id": "opening-1",
        "content": "Tell me about a project.",
        "node_id": state["competency_node"],
        "message_kind": "opening",
    }
    assert svc._append_opening_message_once(state, first) is True
    original = dict(state["active_task_contract"])

    state["user_input"] = "I automated a weekly report."
    assert state["active_task_contract"] == original

    svc._commit_career_task_contract(state, {
        "turn_id": "turn-feedback",
        "content": "Reviewing that answer.",
        "message_kind": "coach_response",
    })
    svc._commit_career_task_contract(state, {
        "turn_id": "turn-fallback",
        "content": "Please send that answer once more.",
        "message_kind": "coach_fallback",
    })
    assert state["active_task_contract"] == original

    second = {
        "message_id": "turn-2",
        "content": "Now use a different stakeholder context.",
        "node_id": state["competency_node"],
        "task_contract": {
            "context_id": "stakeholder-transfer",
            "semantic_anchors": ["stakeholder", "trade-off"],
            "participant_claims": [],
        },
    }
    svc._commit_career_task_contract(state, second)

    assert state["active_task_contract"]["prompt_id"] == "turn-2"
    assert state["active_task_contract"]["context_id"] == "stakeholder-transfer"
    assert state["active_task_contract"]["participant_claims"] == []


def test_visible_gd_and_interview_tasks_derive_runtime_contract_fields():
    gd_state = svc._new_state(
        "user-1",
        "gd-session",
        "gd_08_include_quiet",
        [],
        task_type="gd_prep",
        module_id="group_discussion",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    opening = svc._opening_fallback_text(gd_state, svc.get_node("gd_08_include_quiet"))
    assert svc._append_opening_message_once(gd_state, {
        "message_id": "gd-opening-1",
        "role": "assistant",
        "content": opening,
        "node_id": "gd_08_include_quiet",
        "message_kind": "opening",
    }) is True
    assert gd_state["active_task_contract"]["active_topic"] == "Should remote work be the default?"
    assert gd_state["active_task_contract"]["participant_claims"] == [
        {"participant_id": "maya", "display_name": "Maya", "status": "quiet"}
    ]
    bridge_contract = svc._derived_career_task_payload(gd_state, {
        "content": "Neha, if you'd like, I'd like to hear your take on the customer-impact angle.",
        "node_id": "gd_08_include_quiet",
        "message_kind": "game_prompt",
    })
    assert bridge_contract["participant_claims"] == [
        {"participant_id": "neha", "display_name": "Neha", "status": "quiet"}
    ]
    pressure_bridge_contract = svc._derived_career_task_payload(gd_state, {
        "content": "Maya has relevant customer experience but has not spoken. Invite Maya safely.",
        "node_id": "gd_08_include_quiet",
        "message_kind": "game_prompt",
    })
    assert pressure_bridge_contract["participant_claims"][0]["participant_id"] == "maya"

    interview_state = svc._new_state(
        "user-1",
        "int-session",
        "int_10_close_strong",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    interview_state["pending_prompt_attempt_type"] = "transfer"
    svc._commit_career_task_contract(interview_state, {
        "turn_id": "int-transfer-1",
        "role": "assistant",
        "content": (
            "Transfer task: Close a Platform Engineer interview. Ask about the team's "
            "first-six-month reliability priority and state the value you would bring."
        ),
        "node_id": "int_10_close_strong",
        "message_kind": "coach_response",
    })
    contract = interview_state["active_task_contract"]
    assert contract["active_role"] == "Platform Engineer"
    assert contract["semantic_anchors"][0] == "platform engineer"
    assert "reliability" in contract["semantic_anchors"][1]
    assert contract["hypothetical"] is True


@pytest.mark.parametrize("answer", [
    (
        "I support remote work because research shows it improves productivity by 300%, "
        "so this evidence proves it should be the default."
    ),
    (
        "Hypothetically, a team might save time. Research shows remote work improves "
        "productivity by 300%, so the motion should pass."
    ),
    (
        "Hypothetically, research shows remote work improves productivity by 300% if a team "
        "uses written updates, so the motion should pass."
    ),
])
def test_unsourced_external_number_cannot_become_gd_evidence(answer):
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        module_id="group_discussion",
    )
    state["active_task_contract"] = {
        "prompt_id": "gd-evidence-1",
        "context_id": "remote-work-evidence",
        "active_role": "",
        "active_topic": "Should remote work be the default?",
        "semantic_anchors": [],
        "participant_claims": [],
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": False,
    }
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        answer,
    )

    result = apply_caps(packet, _all_met_eval(packet, answer))

    assert result.pass_eligible is False
    assert "concrete_evidence" in result.required_missing
    assert result.evidence_assessment["evidence_type"] == "unsupported"
    assert result.evidence_assessment["source_status"] == "missing"


def test_lowercase_named_source_can_support_an_adjacent_external_claim():
    assessment = assess_gd_evidence(
        "According to gitlab's public handbook, its teams use documented async decisions. "
        "The company reports that this reduces dependence on meetings."
    )

    assert assessment.evidence_type == "sourced_external"
    assert assessment.source_status == "named"


def test_unrelated_adjacent_source_does_not_validate_an_external_claim():
    assessment = assess_gd_evidence(
        "According to gitlab's public handbook, teams document async decisions. "
        "Research shows remote work improves productivity by 300%."
    )

    assert assessment.evidence_type == "unsupported"
    assert assessment.source_status == "missing"


@pytest.mark.parametrize("answer", [
    (
        "According to GitLab's public handbook, teams document async decisions, "
        "but research shows remote work improves productivity by 300%."
    ),
    "According to an unnamed source, remote work improves productivity by 300%.",
    "According to a person familiar with it, research shows remote work improves productivity by 300%.",
    (
        "According to GitLab's public handbook, its teams document async decisions, "
        "and separately research shows remote work improves productivity by 300%."
    ),
    (
        "According to GitLab's public handbook, teams document async decisions. "
        "It discusses async practices, but research shows remote work improves productivity by 300%."
    ),
])
def test_unrelated_or_placeholder_source_does_not_validate_external_claim(answer):
    assessment = assess_gd_evidence(answer)

    assert assessment.evidence_type == "unsupported"
    assert assessment.source_status == "missing"


def test_gd08_requires_the_assigned_quiet_participant():
    answer = (
        "Neha, could you share your view on whether remote work should be the default, "
        "if you feel comfortable?"
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_08_include_quiet",
        [],
        task_type="gd_prep",
        module_id="group_discussion",
    )
    state["active_task_contract"] = {
        "prompt_id": "gd-quiet-1",
        "context_id": "remote-work-maya-quiet",
        "active_role": "",
        "active_topic": "Should remote work be the default?",
        "semantic_anchors": [],
        "participant_claims": [
            {"participant_id": "maya", "display_name": "Maya", "status": "quiet"}
        ],
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": True,
    }
    packet = build_evaluation_packet(state, svc.get_node("gd_08_include_quiet"), answer)

    result = apply_caps(packet, _all_met_eval(packet, answer))

    assert result.pass_eligible is False
    assert "names_quiet_participant" in result.required_missing

    unrelated_invite = (
        "Remote work improves access, but Maya, would you like to share your thoughts "
        "about cricket?"
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_08_include_quiet"),
        unrelated_invite,
    )
    result = apply_caps(packet, _all_met_eval(packet, unrelated_invite))
    assert result.pass_eligible is False
    assert "topic_linked_invite" in result.required_missing

    topic_linked_invite = (
        "On whether remote work should be the default, Maya, would you like to share "
        "your perspective if you feel comfortable?"
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_08_include_quiet"),
        topic_linked_invite,
    )
    result = apply_caps(packet, _all_met_eval(packet, topic_linked_invite))
    assert "topic_linked_invite" not in result.required_missing


def test_gd10_rejects_two_assigned_claims_with_the_same_stance():
    answer = (
        "Maya supports remote work for access. Dev supports it for flexibility, but Dev says "
        "the remaining risk is manageable. "
        "Their common ground is wider participation, so we should run a measured pilot."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_10_drive_consensus",
        [],
        task_type="gd_prep",
        module_id="group_discussion",
    )
    state["active_task_contract"] = {
        "prompt_id": "gd-consensus-1",
        "context_id": "remote-work-same-stance",
        "active_role": "",
        "active_topic": "Should remote work be the default?",
        "semantic_anchors": [],
        "participant_claims": [
            {"participant_id": "maya", "display_name": "Maya", "claim": "remote work widens access", "stance": "support"},
            {"participant_id": "dev", "display_name": "Dev", "claim": "remote work improves flexibility", "stance": "support"},
        ],
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": True,
    }
    packet = build_evaluation_packet(state, svc.get_node("gd_10_drive_consensus"), answer)

    result = apply_caps(packet, _all_met_eval(packet, answer))

    assert result.pass_eligible is False
    assert "summarizes_key_points" in result.required_missing


def test_gd10_rejects_reversing_the_assigned_stances():
    answer = (
        "Maya says the evidence is too mixed to accept remote work. Dev supports remote work "
        "because it widens access. Both want reliable evidence, so we should run a pilot."
    )
    state = svc._new_state(
        "user-1", "session-1", "gd_10_drive_consensus", [],
        task_type="gd_prep", module_id="group_discussion",
    )
    state["active_task_contract"] = {
        "prompt_id": "gd-consensus-2",
        "context_id": "remote-work-distinct-stances",
        "active_role": "",
        "active_topic": "Should remote work be the default?",
        "semantic_anchors": [],
        "participant_claims": [
            {"participant_id": "maya", "display_name": "Maya", "claim": "the evidence supports remote work", "stance": "support"},
            {"participant_id": "dev", "display_name": "Dev", "claim": "the evidence is too mixed to accept remote work", "stance": "qualified_opposition"},
        ],
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": True,
    }
    packet = build_evaluation_packet(state, svc.get_node("gd_10_drive_consensus"), answer)

    result = apply_caps(packet, _all_met_eval(packet, answer))

    assert result.pass_eligible is False
    assert "summarizes_key_points" in result.required_missing

    combined_reversal = (
        "Maya and Dev disagree: Maya says the evidence is mixed and needs qualification, "
        "while Dev supports remote work because it widens access. "
        "Both want reliable evidence, so run a pilot."
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_10_drive_consensus"),
        combined_reversal,
    )
    result = apply_caps(packet, _all_met_eval(packet, combined_reversal))
    assert result.pass_eligible is False
    assert "summarizes_key_points" in result.required_missing


def test_gd10_rejects_negating_an_assigned_qualification():
    answer = (
        "Maya supports remote work because it widens access. Dev rejects the idea that the "
        "evidence is mixed and supports proceeding immediately. Both want a decision, so we "
        "should adopt the motion now."
    )
    state = svc._new_state(
        "user-1", "session-1", "gd_10_drive_consensus", [],
        task_type="gd_prep", module_id="group_discussion",
    )
    state["active_task_contract"] = {
        "prompt_id": "gd-consensus-3",
        "context_id": "remote-work-negated-qualification",
        "active_role": "",
        "active_topic": "Should remote work be the default?",
        "semantic_anchors": [],
        "participant_claims": [
            {"participant_id": "maya", "display_name": "Maya", "claim": "remote work widens access", "stance": "support"},
            {"participant_id": "dev", "display_name": "Dev", "claim": "the evidence is mixed and needs qualification", "stance": "qualified_opposition"},
        ],
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": True,
    }
    packet = build_evaluation_packet(state, svc.get_node("gd_10_drive_consensus"), answer)

    result = apply_caps(packet, _all_met_eval(packet, answer))

    assert result.pass_eligible is False
    assert "summarizes_key_points" in result.required_missing

    for negated_qualification in (
        "the evidence is no longer mixed",
        "the evidence is hardly mixed",
        "the evidence is not really mixed",
        "Dev disputes that the evidence is mixed",
    ):
        dev_position = (
            negated_qualification
            if negated_qualification.startswith("Dev ")
            else f"Dev says {negated_qualification}"
        )
        answer = (
            "Maya supports remote work because it widens access. "
            f"{dev_position} and supports proceeding immediately. "
            "Both want a decision, so we should adopt it."
        )
        packet = build_evaluation_packet(
            state,
            svc.get_node("gd_10_drive_consensus"),
            answer,
        )
        result = apply_caps(packet, _all_met_eval(packet, answer))
        assert result.pass_eligible is False
        assert "summarizes_key_points" in result.required_missing

    plain_negation = (
        "Maya supports remote work because it widens access. Dev says the evidence is not "
        "mixed and supports proceeding immediately. Both want a decision, so we should adopt it."
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_10_drive_consensus"),
        plain_negation,
    )
    result = apply_caps(packet, _all_met_eval(packet, plain_negation))
    assert result.pass_eligible is False
    assert "summarizes_key_points" in result.required_missing


def test_interview_transfer_uses_visible_contract_anchors_not_static_keywords():
    answer = (
        "I aligned a client stakeholder by explaining the trade-off clearly, "
        "and the partner accepted the proposal."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_02_strength_with_evidence",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state.update({
        "active_prompt_attempt_type": "transfer",
        "core_qualified": True,
        "core_qualification_turn_id": "core-eval-1",
        "core_qualification_evidence": {
            "evaluation_id": "core-eval-1",
            "user_id": "user-1",
            "node_id": "int_02_strength_with_evidence",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": "I stayed calm during an outage and coordinated the rollback.",
            "task_contract": {"context_id": "outage-core"},
        },
        "active_task_contract": {
            "prompt_id": "transfer-retail-1",
            "context_id": "retail-stockout-transfer",
            "active_role": "Store Manager",
            "active_topic": "",
            "semantic_anchors": ["inventory stockout", "store shift"],
            "participant_claims": [],
            "evidence_policy": "learner_owned_or_sourced",
            "hypothetical": True,
        },
    })
    packet = build_evaluation_packet(
        state,
        svc.get_node("int_02_strength_with_evidence"),
        answer,
    )

    result = apply_caps(packet, _all_met_eval(packet, answer))

    assert result.pass_eligible is False
    assert "transfer_context" in result.required_missing


def test_int10_uses_active_role_instead_of_gd_topic_for_role_fit():
    answer = (
        "What would success in remote work look like after six months? "
        "I would bring strong remote collaboration and delivery discipline."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_10_close_strong",
        [],
        task_type="interview_prep",
        module_id="interview",
        career_context={"primary_role": "Data Analyst"},
    )
    state["active_task_contract"] = {
        "prompt_id": "close-1",
        "context_id": "data-analyst-close",
        "active_role": "Data Analyst",
        "active_topic": "remote work",
        "semantic_anchors": [],
        "participant_claims": [],
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": False,
    }
    packet = build_evaluation_packet(state, svc.get_node("int_10_close_strong"), answer)

    result = apply_caps(packet, _all_met_eval(packet, answer))

    assert result.pass_eligible is False
    assert "role_relevance" in result.required_missing


@pytest.mark.asyncio
async def test_core_task_contract_survives_durable_hydration(store):
    store.turn_evaluations.append({
        "evaluation_id": "core-eval-durable",
        "user_id": "user-1",
        "node_id": "int_02_strength_with_evidence",
        "attempt_type": "independent",
        "pass_eligible": True,
        "blockers": [],
        "effective_score": 0.82,
        "user_answer": "I kept a client rollout calm and reduced avoidable rework.",
        "context_json": {
            "task_contract": {
                "prompt_id": "core-prompt-1",
                "context_id": "client-rollout-core",
                "active_role": "Account Manager",
                "active_topic": "",
                "semantic_anchors": [],
                "participant_claims": [],
                "evidence_policy": "learner_owned_or_sourced",
                "hypothetical": False,
            }
        },
    })
    state = svc._new_state(
        "user-1", "session-1", "int_02_strength_with_evidence", [],
        task_type="interview_prep", module_id="interview",
    )
    state["independent_passes"] = 2

    await svc._hydrate_core_qualification(state)

    assert state["core_qualified"] is True
    assert state["core_qualification_evidence"]["task_contract"]["context_id"] == "client-rollout-core"


@pytest.mark.asyncio
async def test_turn_ledger_persists_evaluated_contract_not_replacement_prompt(store):
    state = svc._new_state(
        "user-1", "session-1", "int_02_strength_with_evidence", [],
        task_type="interview_prep", module_id="interview",
    )
    evaluated = {
        "prompt_id": "core-prompt",
        "context_id": "core-context",
        "active_role": "Account Manager",
        "active_topic": "",
        "semantic_anchors": [],
        "participant_claims": [],
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": False,
    }
    replacement = {**evaluated, "prompt_id": "transfer-prompt", "context_id": "transfer-context"}
    state.update({
        "user_input": "I kept a client rollout calm and reduced avoidable rework.",
        "last_diagnosis": {"on_task": True, "english": True, "affect": "neutral", "next_focus": ""},
        "last_eval_score": 0.82,
        "last_rubric_result": {
            "raw_score": 0.82,
            "effective_score": 0.82,
            "criteria": [],
            "required_missing": [],
            "blockers": [],
            "strengths": ["specific learner-owned example"],
            "errors": [],
            "next_focus": "",
            "pass_eligible": True,
            "mastery_eligible": False,
            "attempt_type": "independent",
        },
        "tutor_turn_plan": {},
        "active_turn_id": "turn-1",
        "attempts": 2,
        "last_evaluated_task_contract": evaluated,
        "active_task_contract": replacement,
    })

    await svc._track_turn(state, "int_02_strength_with_evidence")

    assert store.turn_evaluations[-1]["context_json"]["task_contract"]["context_id"] == "core-context"
