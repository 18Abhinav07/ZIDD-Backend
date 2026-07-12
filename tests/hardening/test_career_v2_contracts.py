import dataclasses

import pytest

from app.services import session_service as svc
from app.services.rubric_engine import build_evaluation_packet


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
