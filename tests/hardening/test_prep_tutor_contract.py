import asyncio
import json
import re
from datetime import datetime, timezone

import pytest

from app.ai.schemas import CriterionEval, PrepRubricEval
from app.services import session_service as svc
from app.services.rubric_engine import apply_caps, build_evaluation_packet, compute_attempt_credit
from app.services.content_personalization import render_gd_bridge_exercise
from app.services.tutor_plan import (
    build_tutor_turn_plan,
    decide_int01_next_task,
)
from app.graph.nodes.bridge import personalize_bridge_exercise, select_bridge_exercise


def _run(coro):
    return asyncio.run(coro)


async def _collect_async(stream):
    items = []
    async for item in stream:
        items.append(item)
    return items


def _gd_complete_model_eval(*, include_topic_relevance: bool) -> PrepRubricEval:
    criteria = [
        CriterionEval(id="clear_stance", met=True, quality=0.9, evidence_quote="I support AI"),
        CriterionEval(
            id="concrete_evidence",
            met=True,
            quality=0.9,
            evidence_quote="reduced placement turnaround from 10 days to 6",
        ),
        CriterionEval(
            id="evidence_link",
            met=True,
            quality=0.85,
            evidence_quote="because our campus pilot reduced placement turnaround",
        ),
    ]
    if include_topic_relevance:
        criteria.append(
            CriterionEval(
                id="topic_relevance",
                met=True,
                quality=0.9,
                evidence_quote="AI in campus placements",
            )
        )
    return PrepRubricEval(
        raw_score=0.9,
        criteria=criteria,
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )


def _evaluate_gd_answer_with_calls_module(monkeypatch, outputs, prompts=None):
    from app.ai import calls

    prompts = prompts if prompts is not None else []

    async def fake_structured(prompt, schema):
        assert schema is PrepRubricEval
        prompts.append(prompt)
        return outputs[len(prompts) - 1]

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)
    answer = (
        "I support AI in campus placements because our campus pilot reduced placement "
        "turnaround from 10 days to 6."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    result = _run(
        calls.evaluate_prep_answer(
            svc.get_node("gd_02_support_with_evidence"),
            [],
            answer,
            career_context=state["career_context"],
            state=state,
        )
    )
    return result, prompts


def test_prep_evaluation_valid_first_result_uses_one_structured_call(monkeypatch):
    valid = _gd_complete_model_eval(include_topic_relevance=True)
    valid = valid.model_copy(update={
        "criteria": [
            *valid.criteria,
            CriterionEval(id="unexpected_extra", met=True, quality=1.0, evidence_quote="extra"),
        ]
    })
    result, prompts = _evaluate_gd_answer_with_calls_module(
        monkeypatch,
        [valid],
    )

    assert len(prompts) == 1
    assert [row.id for row in result.criteria] == [
        "clear_stance",
        "concrete_evidence",
        "topic_relevance",
        "evidence_link",
    ]
    assert result.pass_eligible is True


def test_prep_evaluation_repairs_non_verbatim_required_evidence_quote(monkeypatch):
    from app.ai import calls

    answer = (
        "For a skeptical engineering manager, Stripe is specific for me because its "
        "programmable billing APIs support developer workflows. I want my next role "
        "to combine distributed-systems depth with developer impact. As a Backend "
        "Software Engineer, I could contribute idempotent metering and observability."
    )
    state = svc._new_state(
        "user-1",
        "session-why-company-proof-repair",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    parent_id = "session-why-company-proof-repair:turn-core:int_05_why_this_role"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_05_why_this_role",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": (
                "Stripe is specific for me because its programmable billing APIs support "
                "developer workflows and match the backend systems I want to build."
            ),
        },
        "active_prompt_attempt_type": "transfer",
    })
    first = PrepRubricEval(
        raw_score=0.9,
        effective_score=0.9,
        criteria=[
            CriterionEval(
                id="company_specific_fact",
                met=True,
                quality=0.9,
                evidence_quote="Stripe's programmable billing APIs support developer workflows.",
            ),
            CriterionEval(
                id="personal_motivation_link",
                met=True,
                quality=0.9,
                evidence_quote="I want my next role to combine distributed-systems depth with developer impact.",
            ),
            CriterionEval(
                id="role_relevance",
                met=True,
                quality=0.9,
                evidence_quote="As a Backend Software Engineer, I could contribute idempotent metering and observability.",
            ),
            CriterionEval(id="non_generic", met=True, quality=0.9),
            CriterionEval(
                id="transfer_context",
                met=True,
                quality=0.9,
                evidence_quote="For a skeptical engineering manager",
            ),
        ],
        required_missing=[],
        next_focus="Try a pressure check.",
        pass_eligible=True,
        mastery_eligible=False,
    )
    repaired = PrepRubricEval(
        raw_score=0.9,
        effective_score=0.9,
        criteria=[
            CriterionEval(
                id="company_specific_fact",
                met=True,
                quality=0.9,
                evidence_quote="Stripe is specific for me because its programmable billing APIs support developer workflows.",
            ),
            CriterionEval(
                id="non_generic",
                met=True,
                quality=0.9,
                evidence_quote="Stripe is specific for me because its programmable billing APIs support developer workflows.",
            ),
        ],
        required_missing=[],
        next_focus="Try a pressure check.",
        pass_eligible=True,
        mastery_eligible=False,
    )
    prompts = []
    outputs = [first, repaired]

    async def fake_structured(prompt, schema):
        assert schema is PrepRubricEval
        prompts.append(prompt)
        return outputs[len(prompts) - 1]

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)

    result = _run(calls.evaluate_prep_answer(
        svc.get_node("int_05_why_this_role"),
        [],
        answer,
        career_context=state["career_context"],
        state=state,
    ))

    assert len(prompts) == 2
    assert "invalid evidence_quote" in prompts[1]
    assert result.pass_eligible is True
    assert result.required_missing == []
    assert result.blockers == []
    assert result.criteria[0].evidence_quote.startswith("Stripe is specific")


def test_prep_evaluation_repair_preserves_first_response_and_only_supplies_target_row(monkeypatch):
    from app.ai import calls

    first_clear = CriterionEval(
        id="clear_stance",
        met=True,
        quality=0.71,
        evidence_quote="I support AI",
        reason="original stance judgment",
    )
    first_evidence = CriterionEval(
        id="concrete_evidence",
        met=False,
        quality=0.22,
        evidence_quote="",
        reason="original evidence judgment",
    )
    first_link = CriterionEval(
        id="evidence_link",
        met=True,
        quality=0.68,
        evidence_quote="because our campus pilot reduced placement turnaround",
        reason="original evidence-link judgment",
    )
    first = PrepRubricEval(
        raw_score=0.60,
        effective_score=0.58,
        understanding="original aggregate understanding",
        criteria=[first_clear, first_evidence, first_link],
        required_missing=["concrete_evidence"],
        strengths=["original strength"],
        errors=["original error"],
        next_focus="original focus",
        on_task=True,
        english=True,
        affect="confused",
        goodbye=False,
        pass_eligible=False,
        mastery_eligible=False,
    )
    repaired_topic = CriterionEval(
        id="topic_relevance",
        met=True,
        quality=0.83,
        evidence_quote="AI in campus placements",
        reason="repair target judgment",
    )
    repair = PrepRubricEval(
        raw_score=0.99,
        effective_score=0.99,
        understanding="repair tried to overwrite understanding",
        criteria=[
            CriterionEval(
                id="clear_stance",
                met=False,
                quality=0.01,
                reason="repair tried to reverse stance",
            ),
            CriterionEval(
                id="concrete_evidence",
                met=True,
                quality=0.99,
                evidence_quote="reduced placement turnaround from 10 days to 6",
                reason="repair tried to reverse evidence judgment",
            ),
            repaired_topic,
            CriterionEval(id="unexpected_extra", met=True, quality=1.0, evidence_quote="extra"),
        ],
        required_missing=[],
        strengths=["repair strength"],
        errors=[],
        next_focus="repair focus",
        on_task=True,
        english=True,
        affect="confident",
        goodbye=True,
        pass_eligible=True,
        mastery_eligible=True,
    )
    captured = {}
    real_apply_caps = calls.apply_caps

    def capture_apply_caps(packet, raw):
        captured["raw"] = raw
        return real_apply_caps(packet, raw)

    monkeypatch.setattr(calls, "apply_caps", capture_apply_caps)
    result, prompts = _evaluate_gd_answer_with_calls_module(
        monkeypatch,
        [first, repair],
    )

    merged = captured["raw"]
    assert len(prompts) == 2
    assert "repair only" in prompts[1].lower()
    assert "topic_relevance" in prompts[1]
    assert merged.raw_score == 0.60
    assert merged.effective_score == 0.58
    assert merged.understanding == "original aggregate understanding"
    assert merged.required_missing == ["concrete_evidence"]
    assert merged.strengths == ["original strength"]
    assert merged.errors == ["original error"]
    assert merged.next_focus == "original focus"
    assert merged.affect == "confused"
    assert merged.goodbye is False
    assert merged.pass_eligible is False
    assert merged.mastery_eligible is False
    assert [row.id for row in merged.criteria] == [
        "clear_stance",
        "concrete_evidence",
        "topic_relevance",
        "evidence_link",
    ]
    assert merged.criteria[0].model_dump() == first_clear.model_dump()
    assert merged.criteria[1].model_dump() == first_evidence.model_dump()
    assert merged.criteria[2].model_dump() == repaired_topic.model_dump()
    assert merged.criteria[3].model_dump() == first_link.model_dump()
    assert result.raw_score == 0.60
    # Repair isolation is asserted against ``merged`` above. The backend may still
    # reconcile an explicit stance, measured outcome, and evidence link after the
    # model responses have been merged.
    assert result.pass_eligible is True
    assert result.required_missing == []
    assert result.mastery_eligible is False


def test_prep_evaluation_conflicting_duplicate_expected_id_gets_one_repair_call(monkeypatch):
    duplicated = _gd_complete_model_eval(include_topic_relevance=True)
    duplicated = duplicated.model_copy(update={
        "criteria": [
            *duplicated.criteria,
            CriterionEval(
                id="topic_relevance",
                met=False,
                quality=0.1,
                reason="conflicting duplicate",
            ),
        ]
    })
    repair = PrepRubricEval(
        raw_score=0.99,
        criteria=[
            CriterionEval(
                id="topic_relevance",
                met=True,
                quality=0.9,
                evidence_quote="AI in campus placements",
            )
        ],
        pass_eligible=True,
        mastery_eligible=True,
        next_focus="repair-only target",
    )

    result, prompts = _evaluate_gd_answer_with_calls_module(monkeypatch, [duplicated, repair])

    assert len(prompts) == 2
    assert "topic_relevance" in prompts[1]
    assert [row.id for row in result.criteria] == [
        "clear_stance",
        "concrete_evidence",
        "topic_relevance",
        "evidence_link",
    ]
    assert result.raw_score == duplicated.raw_score


@pytest.mark.parametrize(
    "repair_rows",
    [
        pytest.param([], id="target-omitted"),
        pytest.param(
            [
                CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="AI in campus placements"),
                CriterionEval(id="topic_relevance", met=False, quality=0.1, reason="duplicate"),
            ],
            id="target-duplicated",
        ),
    ],
)
def test_prep_evaluation_invalid_repair_target_uses_provable_gd_fallback_without_third_call(
    monkeypatch,
    repair_rows,
):
    prompts = []
    valid_non_targets = [
        row
        for row in _gd_complete_model_eval(include_topic_relevance=True).criteria
        if row.id != "topic_relevance"
    ]
    repair = PrepRubricEval(
        raw_score=0.99,
        criteria=[*valid_non_targets, *repair_rows],
        next_focus="repair-only target",
    )

    result, _ = _evaluate_gd_answer_with_calls_module(
        monkeypatch,
        [
            _gd_complete_model_eval(include_topic_relevance=False),
            repair,
        ],
        prompts,
    )
    assert len(prompts) == 2
    assert result.pass_eligible is True
    assert result.required_missing == []


def test_prep_evaluation_failed_repair_call_uses_provable_gd_fallback(monkeypatch):
    from app.ai import calls

    prompts = []

    async def fake_structured(prompt, schema):
        assert schema is PrepRubricEval
        prompts.append(prompt)
        if len(prompts) == 1:
            return _gd_complete_model_eval(include_topic_relevance=False)
        raise TimeoutError("repair model unavailable")

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)
    answer = (
        "I support AI in campus placements because our campus pilot reduced placement "
        "turnaround from 10 days to 6."
    )
    state = svc._new_state(
        "user-1",
        "session-gd-repair-unavailable",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )

    result = _run(calls.evaluate_prep_answer(
        svc.get_node("gd_02_support_with_evidence"),
        [],
        answer,
        career_context=state["career_context"],
        state=state,
    ))

    assert len(prompts) == 2
    assert result.pass_eligible is True
    assert result.required_missing == []


def test_gd_take_floor_invalid_repair_uses_provable_fallback(monkeypatch):
    from app.ai import calls

    prompts = []

    async def omitted_rows(prompt, schema):
        assert schema is PrepRubricEval
        prompts.append(prompt)
        return PrepRubricEval(
            raw_score=0.0,
            criteria=[],
            next_focus="Use a linked entry.",
            pass_eligible=False,
        )

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", omitted_rows)
    state = svc._new_state(
        "user-1",
        "session-gd-take-floor-fallback",
        "gd_03_take_the_floor",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["messages"].append({
        "role": "assistant",
        "content": "Someone just mentioned remote work improving hiring access. Build on that point.",
    })
    answer = (
        "Building on the point about hiring access, remote work lets us recruit experienced "
        "backend engineers in more regions. That matters because wider coverage makes incident "
        "ownership more resilient while giving remote hires meaningful design responsibility."
    )

    result = _run(calls.evaluate_prep_answer(
        svc.get_node("gd_03_take_the_floor"),
        state["messages"],
        answer,
        career_context=state["career_context"],
        state=state,
    ))

    assert len(prompts) == 2
    assert result.pass_eligible is True
    assert result.required_missing == []


@pytest.mark.parametrize(
    ("node_id", "prompt", "answer"),
    [
        pytest.param(
            "gd_01_stake_position",
            'State your position on the motion: "Should remote work be the default?"',
            "I believe remote coffee should be mandatory.",
            id="stance-topic-word-stuffing",
        ),
        pytest.param(
            "gd_03_take_the_floor",
            "Someone just said remote work improves hiring access. Enter and add one implication.",
            (
                "Building on remote work and hiring access, coffee access improves morale because "
                "warm drinks help employees stay alert during long meetings."
            ),
            id="take-floor-unrelated-extension",
        ),
        pytest.param(
            "gd_05_disagree_respectfully",
            "A participant argues that remote work improves hiring access. Disagree respectfully.",
            (
                "I agree that remote work can help. However, coffee should be free because "
                "employees need warm drinks during long meetings and early shifts."
            ),
            id="disagreement-unrelated-counterpoint",
        ),
        pytest.param(
            "gd_02_support_with_evidence",
            'Motion: "Should remote work be the default?" State a position and support it.',
            (
                "I support remote work as the default. Our coffee pilot reduced afternoon "
                "tiredness by 20%, so this evidence shows why free coffee matters."
            ),
            id="evidence-unrelated-to-stance",
        ),
        pytest.param(
            "gd_04_build_on_others",
            "A participant said remote work improves hiring access. Credit that point and extend it.",
            (
                "Building on that point about remote work improving hiring access, I would add "
                "that coffee should be free because warm drinks improve morale during long meetings."
            ),
            id="build-on-unrelated-extension",
        ),
    ],
)
def test_gd_structural_fallback_does_not_credit_topic_stuffing(
    monkeypatch,
    node_id,
    prompt,
    answer,
):
    from app.ai import calls

    call_count = 0

    async def incomplete_then_timeout(_prompt, _schema):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return PrepRubricEval(
                raw_score=0.0,
                criteria=[],
                required_missing=[],
                next_focus="Evaluator omitted rows.",
                pass_eligible=False,
            )
        raise TimeoutError("repair unavailable")

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", incomplete_then_timeout)
    state = svc._new_state(
        "user-1",
        f"session-{node_id}-topic-stuffing",
        node_id,
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["messages"] = [{"role": "assistant", "content": prompt}]

    with pytest.raises(calls.PrepEvaluationRetryRequired):
        _run(calls.evaluate_prep_answer(
            svc.get_node(node_id),
            state["messages"],
            answer,
            career_context=state["career_context"],
            state=state,
        ))

    assert call_count == 2


def test_gd_node_without_provable_reconciler_retries_failed_structural_repair(monkeypatch):
    from app.ai import calls

    call_count = 0

    async def incomplete_then_timeout(_prompt, _schema):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return PrepRubricEval(
                raw_score=0.0,
                criteria=[],
                required_missing=[],
                next_focus="Evaluator omitted rows.",
                pass_eligible=False,
            )
        raise TimeoutError("repair unavailable")

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", incomplete_then_timeout)
    state = svc._new_state(
        "user-1",
        "session-gd06-repair-retry",
        "gd_06_balanced_view",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )

    with pytest.raises(calls.PrepEvaluationRetryRequired):
        _run(calls.evaluate_prep_answer(
            svc.get_node("gd_06_balanced_view"),
            [],
            (
                "Remote work expands access, while weak onboarding can isolate new hires. "
                "Access matters more, so it should be the default with onboarding safeguards."
            ),
            career_context=state["career_context"],
            state=state,
        ))

    assert call_count == 2


def test_prep_evaluation_pitch_omissions_use_deterministic_fallback_after_one_repair(monkeypatch):
    from app.ai import calls

    prompts = []

    incomplete = PrepRubricEval(
        raw_score=0.80,
        criteria=[
            CriterionEval(id="pitch_structure", met=False, quality=0.2, reason="missing structure"),
            CriterionEval(id="future_goal", met=False, quality=0.2, reason="missing future goal"),
        ],
        pass_eligible=True,
        mastery_eligible=False,
        next_focus="missing structural rows",
    )
    outputs = [incomplete, incomplete]

    async def fake_structured(prompt, schema):
        assert schema is PrepRubricEval
        prompts.append(prompt)
        return outputs[len(prompts) - 1]

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)
    answer = (
        "I’m a backend software engineer focused on reliable payment and event-driven systems. "
        "My strength is turning failure-prone workflows into observable, resilient services; in a recent "
        "payments migration, I used idempotency and staged rollout controls to cut duplicate writes by 96% "
        "and reduce status latency from 18 seconds to 4. I’m now looking to own larger distributed systems "
        "where reliability improvements directly protect revenue and customer trust."
    )
    state = svc._new_state(
        "user-1",
        "session-pitch-structural-retry",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )

    result = _run(
        calls.evaluate_prep_answer(
            svc.get_node("int_01_elevator_pitch"),
            [],
            answer,
            career_context=state["career_context"],
            state=state,
        )
    )

    assert len(prompts) == 2
    assert "answers_question" in prompts[1]
    assert result.pass_eligible is True
    assert result.required_missing == []


def test_complete_pitch_uses_existing_deterministic_evidence_after_structural_repair_fails(monkeypatch):
    """A Flash-Lite rubric omission must not force a learner to repeat a valid pitch."""
    from app.ai import calls

    answer = (
        "I am a backend software engineer who builds reliable APIs. In a recent project, "
        "I designed a payment workflow with idempotency checks so duplicate requests could "
        "not charge users twice. I want to bring that focus on reliability and clear user "
        "impact to a backend engineering role."
    )
    state = svc._new_state(
        "user-1",
        "session-pitch-fallback",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    call_count = 0

    async def incomplete_then_timeout(_prompt, _schema):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return PrepRubricEval(
                raw_score=0.2,
                criteria=[],
                required_missing=[],
                next_focus="Evaluator omitted rows.",
                pass_eligible=False,
            )
        raise TimeoutError("repair unavailable")

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", incomplete_then_timeout)

    result = _run(
        calls.evaluate_prep_answer(
            svc.get_node("int_01_elevator_pitch"),
            [],
            answer,
            career_context=state["career_context"],
            state=state,
        )
    )

    assert call_count == 2
    assert result.pass_eligible is True
    assert result.required_missing == []
    assert result.blockers == []


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


def test_pass_ineligible_rubric_attempt_cannot_raise_mastery_or_readiness():
    from app.graph.nodes import evaluate as eval_node

    state = svc._new_state(
        "user-1",
        "session-failed-attempt-no-growth",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    state.update({"current_mastery": 0.2, "readiness_score": 0.25})
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "I support referral hiring because our pilot reduced turnover by 20 percent.",
    )
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.9,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.9, evidence_quote="I support referral hiring"),
                CriterionEval(id="concrete_evidence", met=True, quality=0.9, evidence_quote="our pilot reduced turnover by 20 percent"),
                CriterionEval(id="topic_relevance", met=False, quality=0.3, reason="does not address AI"),
                CriterionEval(id="evidence_link", met=True, quality=0.9, evidence_quote="because our pilot reduced turnover by 20 percent"),
            ],
            required_missing=["topic_relevance"],
            next_focus="Address the AI-screening part of the motion.",
            pass_eligible=False,
        ),
    )

    updates = eval_node._result(
        state,
        eval_node._diagnosis_from_rubric(result),
        smooth=False,
        rubric_result=result,
    )
    progress = compute_attempt_credit(
        {"readiness_score": state["readiness_score"]},
        result,
    )

    assert result.pass_eligible is False
    assert any(
        blocker.startswith(("evaluator_incomplete:", "missing_required:"))
        for blocker in result.blockers
    )
    assert result.effective_score > state["current_mastery"]
    assert updates["current_mastery"] == state["current_mastery"]
    assert progress["readiness_score"] == state["readiness_score"]


def test_pass_eligible_rubric_attempt_can_raise_mastery_and_readiness():
    from app.graph.nodes import evaluate as eval_node

    state = svc._new_state(
        "user-1",
        "session-passing-attempt-growth",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    state.update({"current_mastery": 0.2, "readiness_score": 0.25})
    answer = (
        "I support AI in hiring because, in a screening pilot I ran, I measured review time "
        "falling by 20 percent, "
        "which shows automated ranking can help when people retain final oversight."
    )
    result = apply_caps(
        build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer),
        PrepRubricEval(
            raw_score=0.9,
            criteria=[
                CriterionEval(id="clear_stance", met=True, quality=0.9, evidence_quote="I support AI in hiring"),
                CriterionEval(id="concrete_evidence", met=True, quality=0.9, evidence_quote="in a screening pilot I ran, I measured review time falling by 20 percent"),
                CriterionEval(id="topic_relevance", met=True, quality=0.9, evidence_quote="AI in hiring"),
                CriterionEval(id="evidence_link", met=True, quality=0.9, evidence_quote="which shows automated ranking can help"),
            ],
            next_focus="Try the skill on a different motion.",
            pass_eligible=True,
        ),
    )

    updates = eval_node._result(
        state,
        eval_node._diagnosis_from_rubric(result),
        smooth=False,
        rubric_result=result,
    )
    progress = compute_attempt_credit(
        {"readiness_score": state["readiness_score"]},
        result,
    )

    assert result.pass_eligible is True
    assert updates["current_mastery"] > state["current_mastery"]
    assert progress["readiness_score"] > state["readiness_score"]


def test_gd_evidence_pressure_reconciles_browser_proven_explicit_defense():
    state = svc._new_state(
        "user-1",
        "session-gd-evidence-pressure",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-gd-evidence-pressure:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_02_support_with_evidence",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should companies use AI in hiring?",
            "learner_answer": "AI should support hiring decisions. Our pilot caught a filter excluding nontraditional titles, so humans kept final review.",
        },
        "active_prompt_attempt_type": "pressure",
        "messages": [
            {
                "role": "user",
                "content": "AI should support hiring decisions. Our pilot caught a filter excluding nontraditional titles, so humans kept final review.",
            },
            {
                "role": "assistant",
                "content": "Diverse training data can remove bias. Why is human review still necessary?",
            },
        ],
    })
    answer = (
        "Diverse training data can reduce bias, but it cannot guarantee that a model's proxy signals are fair. "
        "In our pilot, the model missed qualified candidates with nontraditional titles; only cohort audits and "
        "human review exposed that pattern. That evidence supports AI for faster ranking, while final selection "
        "remains accountable to people."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.6,
        effective_score=0.6,
        criteria=[
            CriterionEval(id="pressure_response", met=False, quality=0.3, reason="link not explicit"),
            CriterionEval(id="evidence_defense", met=False, quality=0.3, reason="evidence not linked"),
            CriterionEval(id="core_consistency", met=False, quality=0.3, reason="core stance unclear"),
        ],
        required_missing=["pressure_response", "evidence_defense", "core_consistency"],
        errors=["missing required rubric proof"],
        next_focus="Explain the link again.",
        on_task=True,
        english=True,
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert result.pass_eligible is True
    assert result.effective_score >= packet.pass_score
    assert result.required_missing == []
    assert result.blockers == []
    assert {row.id for row in result.criteria if row.met} == {
        "pressure_response", "evidence_defense", "core_consistency"
    }


def test_shared_gd_pressure_reconciles_explicit_distinct_implication():
    state = svc._new_state(
        "user-1",
        "session-gd-build-pressure",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-gd-build-pressure:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_04_build_on_others",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should remote work be the default?",
            "learner_answer": (
                "Building on the Analyst's point that implementation should be measurable, I would add "
                "a 90-day remote-work pilot with onboarding, decision-latency, engagement, and attrition "
                "thresholds, plus mentorship and in-person resets when junior employees fall behind."
            ),
        },
        "active_prompt_attempt_type": "pressure",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Building on the hiring-access point, remote work widens the candidate pool. "
                    "I would add that inclusion still requires structured onboarding and promotion audits."
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "You merely repeated the prior idea. Credit the exact part you used, then state "
                    "the new implication you added."
                ),
            },
        ],
    })
    answer = (
        "The exact point I used was the Analyst's claim that implementation should be measurable. "
        "My added implication was a 90-day remote-work pilot with onboarding, decision-latency, "
        "engagement, and attrition thresholds, plus automatic mentorship and in-person resets "
        "when junior employees fall behind."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_04_build_on_others"), answer)
    raw = PrepRubricEval(
        raw_score=0.6,
        criteria=[
            CriterionEval(id="pressure_response", met=False, quality=0.3, reason="not direct"),
            CriterionEval(id="evidence_defense", met=False, quality=0.3, reason="not concrete"),
            CriterionEval(id="core_consistency", met=False, quality=0.3, reason="not linked"),
        ],
        required_missing=["pressure_response", "evidence_defense", "core_consistency"],
        next_focus="Answer the pressure again.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is True
    assert result.required_missing == []
    assert result.blockers == []


def test_shared_gd_pressure_does_not_pass_generic_disagreement():
    state = svc._new_state(
        "user-1",
        "session-gd-build-pressure-thin",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-gd-build-pressure-thin:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_04_build_on_others",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
        },
        "active_prompt_attempt_type": "pressure",
    })
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_04_build_on_others"),
        "I disagree. My idea is different and better.",
    )
    raw = PrepRubricEval(
        raw_score=0.4,
        criteria=[],
        required_missing=["pressure_response", "evidence_defense", "core_consistency"],
        next_focus="Give a concrete response.",
        pass_eligible=False,
    )

    assert apply_caps(packet, raw).pass_eligible is False


def test_core_qualification_stores_the_actual_independent_answer():
    state = svc._new_state(
        "user-1",
        "session-core-answer-evidence",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    answer = (
        "Building on the hiring-access point, remote work widens the candidate pool. "
        "I would add that inclusion requires structured onboarding and promotion audits."
    )
    state.update({
        "user_input": answer,
        "active_turn_id": "turn-core",
        "independent_passes": 1,
        "last_eval_score": 0.86,
        "last_clean_pass_score": 0.86,
        "last_diagnosis": {"english": True, "on_task": True},
        "last_rubric_result": {
            "effective_score": 0.86,
            "pass_eligible": True,
            "mastery_eligible": False,
            "attempt_type": "independent",
            "required_missing": [],
            "blockers": [],
            "criteria": [],
            "next_focus": "Try a transfer.",
        },
    })

    svc._update_progress(state)

    assert state["core_qualified"] is True
    assert state["core_qualification_evidence"]["learner_answer"] == answer
    assert state["core_qualification_evidence"]["active_topic"] == "Should remote work be the default?"


def test_shared_gd_pressure_consistency_uses_qualified_answer_not_latest_user_turn():
    state = svc._new_state(
        "user-1",
        "session-pressure-qualified-answer",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-pressure-qualified-answer:core"
    qualified_answer = (
        "Building on the hiring-access point, remote work widens the candidate pool. "
        "I would add that inclusion requires structured onboarding and promotion audits."
    )
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_04_build_on_others",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should remote work be the default?",
            "learner_answer": qualified_answer,
        },
        "active_prompt_attempt_type": "pressure",
        "messages": [
            {"role": "user", "content": "A four-day schedule can improve focus when support coverage is preserved."},
            {"role": "assistant", "content": "You merely repeated the hiring-access point. What distinct inclusion safeguard did you add?"},
        ],
    })
    answer = (
        "You are right that I used the hiring-access point. The distinct implication is that remote "
        "inclusion requires structured onboarding and promotion audits, because a wider candidate "
        "pool does not guarantee equitable participation."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_04_build_on_others"), answer)
    raw = PrepRubricEval(
        raw_score=0.6,
        criteria=[
            CriterionEval(id="pressure_response", met=False, quality=0.2),
            CriterionEval(id="evidence_defense", met=False, quality=0.2),
            CriterionEval(id="core_consistency", met=False, quality=0.2),
        ],
        required_missing=["pressure_response", "evidence_defense", "core_consistency"],
        next_focus="Defend the qualified answer.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is True
    assert result.required_missing == []


def test_shared_gd_pressure_does_not_credit_an_exclusive_opposite_position():
    state = svc._new_state(
        "user-1",
        "session-pressure-opposite-position",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-pressure-opposite-position:core"
    qualified_answer = (
        "Building on the hiring-access point, remote work widens the candidate pool. "
        "I would add structured onboarding and promotion audits."
    )
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_04_build_on_others",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should remote work be the default?",
            "learner_answer": qualified_answer,
        },
        "active_prompt_attempt_type": "pressure",
        "messages": [{
            "role": "assistant",
            "content": (
                "You merely repeated the hiring-access point. What distinct inclusion "
                "safeguard did you add?"
            ),
        }],
    })
    answer = (
        "You are right that remote work can widen hiring access, but office work is the "
        "only viable model because onboarding, mentorship, and decision ownership need "
        "in-person teams. The implication is a 90-day office-first pilot with engagement "
        "and attrition thresholds, not a remote default."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_04_build_on_others"), answer)
    raw = PrepRubricEval(
        raw_score=0.6,
        criteria=[
            CriterionEval(id="pressure_response", met=False, quality=0.2),
            CriterionEval(id="evidence_defense", met=False, quality=0.2),
            CriterionEval(id="core_consistency", met=False, quality=0.2),
        ],
        required_missing=["pressure_response", "evidence_defense", "core_consistency"],
        next_focus="Defend the qualified answer.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    assert "core_consistency" in result.required_missing


def test_shared_gd_pressure_legacy_evidence_fails_closed_on_core_consistency():
    state = svc._new_state(
        "user-1",
        "session-pressure-legacy-core",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-pressure-legacy-core:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_04_build_on_others",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should remote work be the default?",
        },
        "active_prompt_attempt_type": "pressure",
        "messages": [
            {"role": "user", "content": "Remote work widens the candidate pool but needs structured onboarding and promotion audits."},
            {"role": "assistant", "content": "You merely repeated the candidate-pool point. What inclusion safeguard did you add?"},
        ],
    })
    answer = (
        "You are right that I used the candidate-pool point. The inclusion safeguard is structured "
        "onboarding and promotion audits, because remote access alone does not guarantee equitable participation."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_04_build_on_others"), answer)
    raw = PrepRubricEval(
        raw_score=0.8,
        criteria=[
            CriterionEval(id="pressure_response", met=False, quality=0.2),
            CriterionEval(id="evidence_defense", met=False, quality=0.2),
            CriterionEval(id="core_consistency", met=False, quality=0.2),
        ],
        required_missing=["pressure_response", "evidence_defense", "core_consistency"],
        next_focus="Defend the qualified answer.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    assert "core_consistency" in result.required_missing


def test_gd_evidence_reconciliation_does_not_pass_generic_unsupported_claim():
    state = svc._new_state(
        "user-1",
        "session-gd-evidence-thin",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    answer = "I support remote work because it is clearly better for everyone."
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.55,
        effective_score=0.55,
        criteria=[
            CriterionEval(id="clear_stance", met=True, quality=0.7, evidence_quote="I support remote work"),
            CriterionEval(id="concrete_evidence", met=False, quality=0.1, reason="no concrete evidence"),
            CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="remote work"),
            CriterionEval(id="evidence_link", met=False, quality=0.2, reason="unsupported claim"),
        ],
        required_missing=["concrete_evidence"],
        next_focus="Add one concrete example or result.",
        on_task=True,
        english=True,
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert result.pass_eligible is False
    assert "concrete_evidence" in result.required_missing


def test_gd_evidence_topic_relevance_does_not_pass_on_generic_hiring_token():
    state = svc._new_state(
        "user-1",
        "session-gd-evidence-off-topic-hiring",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    answer = (
        "I support referral hiring because our campus pilot increased retention by 20 percent. "
        "That evidence shows personal referrals can improve team stability."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    raw = PrepRubricEval(
        raw_score=0.86,
        criteria=[
            CriterionEval(id="clear_stance", met=True, quality=0.85, evidence_quote="I support referral hiring"),
            CriterionEval(id="concrete_evidence", met=True, quality=0.85, evidence_quote="our campus pilot increased retention by 20 percent"),
            CriterionEval(id="topic_relevance", met=False, quality=0.2, reason="AI is not addressed"),
            CriterionEval(id="evidence_link", met=True, quality=0.85, evidence_quote="That evidence shows personal referrals can improve team stability"),
        ],
        required_missing=["topic_relevance"],
        next_focus="Address AI screening, not hiring generally.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    assert "topic_relevance" in result.required_missing


def test_gd_evidence_topic_relevance_accepts_both_ai_and_hiring_signals():
    state = svc._new_state(
        "user-1",
        "session-gd-evidence-grounded-ai-hiring",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    answer = (
        "I support AI screening in hiring because our pilot reduced shortlist review time by 20 percent. "
        "That evidence supports automated ranking while recruiters retain final oversight."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_02_support_with_evidence"), answer)
    raw = PrepRubricEval(
        raw_score=0.86,
        criteria=[
            CriterionEval(id="clear_stance", met=True, quality=0.85, evidence_quote="I support AI screening in hiring"),
            CriterionEval(id="concrete_evidence", met=True, quality=0.85, evidence_quote="our pilot reduced shortlist review time by 20 percent"),
            CriterionEval(id="topic_relevance", met=False, quality=0.2, reason="topic proof omitted"),
            CriterionEval(id="evidence_link", met=True, quality=0.85, evidence_quote="That evidence supports automated ranking"),
        ],
        required_missing=["topic_relevance"],
        next_focus="Address the motion.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is True
    assert result.required_missing == []


def test_gd_evidence_partial_feedback_repairs_gap_without_advancing_stage():
    state = svc._new_state(
        "user-1",
        "session-gd-evidence-partial-feedback",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state.update({
        "user_input": "Our pilot caught a biased filter, so final hiring decisions need human review.",
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["evidence_link"],
            "blockers": ["missing_required:evidence_link"],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "partial",
            "next_action": "rewrite",
            "allowed_praise": False,
        },
    })

    text = svc._gd02_feedback_text(state)

    assert "pressure" not in text.lower()
    assert "same evidence" in text.lower()
    assert "why the same evidence supports" in text.lower()
    assert state.get("pending_prompt_attempt_type") is None


def test_gd_evidence_pass_feedback_returns_pressure_to_qualified_core_topic():
    state = svc._new_state(
        "user-1",
        "session-gd-evidence-pressure-feedback",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state.update({
        "user_input": "Our AI hiring pilot caught a biased title filter, so humans retained final review.",
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "core_qualified": True,
        "core_qualification_turn_id": "session-gd-evidence-pressure-feedback:core",
        "core_qualification_evidence": {
            "evaluation_id": "session-gd-evidence-pressure-feedback:core",
            "user_id": "user-1",
            "node_id": "gd_02_support_with_evidence",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": "Remote work expands hiring reach across regions.",
            "active_topic": "Should remote work be the default?",
        },
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_pressure",
            "allowed_praise": False,
        },
    })

    text = svc._gd02_feedback_text(state)

    assert "pressure check" in text.lower()
    assert "Should remote work be the default?" in text
    assert state["pending_prompt_attempt_type"] == "pressure"
    assert state["pending_gd_prompt_topic"] == "Should remote work be the default?"


def test_gd_evidence_corrupt_pressure_plan_without_core_requalifies_independently():
    state = svc._new_state(
        "user-1",
        "session-gd-evidence-invalid-pressure-parent",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state.update({
        "user_input": "Our AI hiring pilot caught a biased filter, so humans retained final review.",
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_pressure",
            "allowed_praise": False,
        },
    })

    text = svc._gd02_feedback_text(state)

    assert "next check" in text.lower()
    assert "pressure check" not in text.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_gd_evaluation_packet_prefers_backend_owned_active_prompt_topic():
    state = svc._new_state(
        "user-1",
        "session-gd-active-topic",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["active_gd_prompt_topic"] = "Should companies use AI in hiring?"

    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "Companies should use AI only for ranking because our pilot caught a biased filter.",
    )

    assert packet.active_topic == "Should companies use AI in hiring?"


def test_gd_evaluation_packet_recovers_topic_from_existing_transfer_prompt():
    state = svc._new_state(
        "user-1",
        "session-gd-recover-transfer-topic",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["messages"].append({
        "role": "assistant",
        "content": (
            "Imagine you're discussing whether companies should be allowed to use AI in "
            "hiring processes. Take a position and support it with one concrete example."
        ),
    })

    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        "AI may rank candidates, but people must decide because our pilot exposed title bias.",
    )

    assert packet.active_topic == "Should companies be allowed to use AI in hiring processes?"
    assert svc._gd_prompt_topic_for_state(state) == packet.active_topic


def test_gd_evaluation_packet_prefers_latest_visible_transfer_over_stale_active_topic():
    state = svc._new_state(
        "user-1",
        "session-gd-visible-transfer-topic",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    state.update({
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "messages": [
            {
                "role": "assistant",
                "node_id": "gd_05_disagree_respectfully",
                "content": (
                    "In your answer about AI hiring, you conceded a valid point. "
                    'Transfer task on "Should remote work be the default?": '
                    "concede one benefit, then disagree."
                ),
            },
            {
                "role": "user",
                "node_id": "gd_05_disagree_respectfully",
                "content": "I agree remote work broadens access, but weak onboarding can harm teams.",
            },
        ],
    })

    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_05_disagree_respectfully"),
        "I agree remote work broadens access, but weak onboarding can harm teams.",
    )

    assert packet.active_topic == "Should remote work be the default?"


def test_gd_topic_inference_recovers_ai_hiring_from_argument_opening():
    state = svc._new_state(
        "user-1",
        "session-gd-ai-opening-topic",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["messages"].append({
        "role": "assistant",
        "content": (
            "Imagine a scenario where someone argues that companies should use AI in hiring "
            "because it reduces human bias. Disagree respectfully."
        ),
    })

    assert svc._gd_prompt_topic_for_state(state) == "Should companies use AI in hiring?"


def test_gd_transfer_motion_skips_same_semantic_topic_family():
    state = svc._new_state(
        "user-1",
        "session-gd-semantic-transfer",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={
            "gd_topics": [
                "Should companies be allowed to use AI in hiring?",
                "Should remote work be the default?",
            ]
        },
    )

    next_topic = svc._next_gd_transfer_motion(
        state,
        "Should companies use AI in hiring only with human oversight?",
    )

    assert next_topic == "Should remote work be the default?"


def test_gd_transfer_repair_excludes_core_and_failed_active_topic_families():
    state = svc._new_state(
        "user-1",
        "session-gd-transfer-repair-cycle",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={
            "gd_topics": [
                "Should companies be allowed to use AI in hiring?",
                "Should remote work be the default?",
            ]
        },
    )
    parent_id = "session-gd-transfer-repair-cycle:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_05_disagree_respectfully",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should companies use AI in hiring?",
            "learner_answer": (
                "I agree AI screening can improve consistency, but models can scale historical "
                "bias without cohort audits and human review."
            ),
        },
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should remote work be the default?",
        "messages": [
            {
                "role": "assistant",
                "node_id": "gd_04_build_on_others",
                "content": "Motion: \"Should digital payments become the default?\"",
            },
            {
                "role": "assistant",
                "node_id": "gd_05_disagree_respectfully",
                "content": "A participant argues companies should use AI in hiring because it reduces bias.",
            },
            {
                "role": "assistant",
                "node_id": "gd_05_disagree_respectfully",
                "content": "Transfer task on remote work: concede one benefit, then disagree.",
            },
        ],
    })

    next_topic = svc._next_gd_transfer_motion(
        state,
        "Should remote work be the default?",
    )

    assert state["core_qualification_evidence"]["active_topic"] == (
        "Should companies use AI in hiring?"
    )
    assert svc.gd_topic_family(next_topic) not in {"ai_hiring", "remote_work"}


def test_gd_same_family_transfer_is_blocked_using_opening_topic_recovery():
    from app.graph.nodes import evaluate as eval_node

    state = svc._new_state(
        "user-1",
        "session-gd-invalid-same-family-transfer",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-gd-invalid-same-family-transfer:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_05_disagree_respectfully",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should companies use AI in hiring?",
            "learner_answer": (
                "I agree AI screening can improve consistency, but models can scale historical "
                "bias without cohort audits and human review."
            ),
        },
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should companies be allowed to use AI in hiring?",
        "messages": [
            {
                "role": "assistant",
                "content": "A participant argues companies should use AI in hiring because it reduces bias.",
            },
            {
                "role": "user",
                "content": "I agree consistent screening can help, but models can scale historical bias.",
            },
            {
                "role": "assistant",
                "content": "Transfer task: should companies be allowed to use AI in hiring?",
            },
        ],
    })
    answer = (
        "I agree that AI screening can improve consistency. However, it can scale historical bias, "
        "so companies still need cohort audits and human review."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_05_disagree_respectfully"), answer)
    raw = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="acknowledges_valid_point", met=True, quality=0.9, evidence_quote="I agree that AI screening can improve consistency"),
            CriterionEval(id="clear_counter", met=True, quality=0.9, evidence_quote="However, it can scale historical bias"),
            CriterionEval(id="reasoned_basis", met=True, quality=0.9, evidence_quote="so companies still need cohort audits and human review"),
            CriterionEval(id="civil_tone", met=True, quality=0.9, evidence_quote="I agree that AI screening can improve consistency"),
            CriterionEval(id="transfer_context", met=True, quality=0.9, evidence_quote="AI screening can improve consistency"),
        ],
        next_focus="Pressure test.",
        pass_eligible=True,
    )

    result = apply_caps(packet, raw)

    assert packet.core_qualification_evidence["active_topic"] == "Should companies use AI in hiring?"
    assert state["core_qualification_evidence"]["active_topic"] == "Should companies use AI in hiring?"
    assert result.pass_eligible is False
    assert "minimum_gate:transfer_context" in result.blockers

    state.update({
        "current_mastery": 0.71,
        "attempts": 5,
        "session_attempts": 4,
        "readiness_score": 0.85,
        "clean_streak": 2,
        "last_rubric_result": result.model_dump(),
        "last_eval_score": result.effective_score,
        "last_clean_pass_score": result.raw_score,
        "last_diagnosis": {"english": True, "on_task": True},
    })
    updates = eval_node._result(
        state,
        eval_node._diagnosis_from_rubric(result),
        smooth=False,
        rubric_result=result,
    )

    assert updates["current_mastery"] == 0.71
    assert updates["attempts"] == 5
    assert updates["session_attempts"] == 4
    svc._update_progress(state)
    assert state["readiness_score"] == 0.85
    assert state["clean_streak"] == 2


def test_gd_cross_family_transfer_reconciles_context_from_topics_and_answer():
    state = svc._new_state(
        "user-1",
        "session-gd-valid-cross-family-transfer",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-gd-valid-cross-family-transfer:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_05_disagree_respectfully",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should companies use AI in hiring?",
            "learner_answer": (
                "I agree AI screening can make hiring more consistent, but models can scale "
                "historical bias without cohort audits and human review."
            ),
        },
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should remote work be the default?",
        "messages": [
            {
                "role": "assistant",
                "content": "A participant argues companies should use AI in hiring because it reduces bias.",
            },
            {
                "role": "assistant",
                "content": "Transfer task on remote work: concede one benefit, then disagree.",
            },
        ],
    })
    answer = (
        "I agree that remote work improves hiring access beyond office hubs. However, it should "
        "not always be the default because weak onboarding and mentoring can harm distributed teams."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_05_disagree_respectfully"), answer)
    raw = PrepRubricEval(
        raw_score=0.85,
        criteria=[
            CriterionEval(id="acknowledges_valid_point", met=True, quality=0.85, evidence_quote="I agree that remote work improves hiring access beyond office hubs"),
            CriterionEval(id="clear_counter", met=True, quality=0.85, evidence_quote="However, it should not always be the default"),
            CriterionEval(id="reasoned_basis", met=True, quality=0.85, evidence_quote="because weak onboarding and mentoring can harm distributed teams"),
            CriterionEval(id="civil_tone", met=True, quality=0.85, evidence_quote="I agree that remote work improves hiring access beyond office hubs"),
            CriterionEval(id="transfer_context", met=False, quality=0.2, reason="context not proven"),
        ],
        required_missing=["transfer_context"],
        next_focus="Use a different context.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert packet.core_qualification_evidence["active_topic"] == "Should companies use AI in hiring?"
    assert result.pass_eligible is True
    assert result.required_missing == []


@pytest.mark.parametrize(
    ("core_topic", "active_topic"),
    [
        ("", "Should remote work be the default?"),
        ("Should companies use AI in hiring?", ""),
        ("hiring", "policy"),
    ],
)
def test_gd_transfer_fails_closed_when_topics_are_missing_or_unverifiable(
    core_topic,
    active_topic,
):
    state = svc._new_state(
        "user-1",
        "session-gd-transfer-unverifiable",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": [active_topic] if active_topic else []},
    )
    parent_id = "session-gd-transfer-unverifiable:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_05_disagree_respectfully",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": core_topic,
            "learner_answer": "I agree AI screening can help hiring, but models can scale historical bias.",
        },
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": active_topic,
        "messages": [],
    })
    answer = (
        "I agree remote work can broaden hiring access. However, it should not always be the default "
        "because weak onboarding can isolate distributed employees."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_05_disagree_respectfully"), answer)
    raw = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="acknowledges_valid_point", met=True, quality=0.9, evidence_quote="I agree remote work can broaden hiring access"),
            CriterionEval(id="clear_counter", met=True, quality=0.9, evidence_quote="However, it should not always be the default"),
            CriterionEval(id="reasoned_basis", met=True, quality=0.9, evidence_quote="because weak onboarding can isolate distributed employees"),
            CriterionEval(id="civil_tone", met=True, quality=0.9, evidence_quote="I agree remote work can broaden hiring access"),
            CriterionEval(id="transfer_context", met=True, quality=0.9, evidence_quote="remote work can broaden hiring access"),
        ],
        next_focus="Try pressure.",
        pass_eligible=True,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    assert "minimum_gate:transfer_context" in result.blockers


def test_gd_transfer_with_verifiable_distinct_topics_remains_eligible():
    state = svc._new_state(
        "user-1",
        "session-gd-transfer-verifiable",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-gd-transfer-verifiable:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_05_disagree_respectfully",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should companies use AI in hiring?",
            "learner_answer": "I agree AI screening can help hiring, but models can scale historical bias.",
        },
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should remote work be the default?",
    })
    answer = (
        "I agree remote work can broaden hiring access. However, it should not always be the default "
        "because weak onboarding can isolate distributed employees."
    )
    result = apply_caps(
        build_evaluation_packet(state, svc.get_node("gd_05_disagree_respectfully"), answer),
        PrepRubricEval(
            raw_score=0.9,
            criteria=[
                CriterionEval(id="acknowledges_valid_point", met=True, quality=0.9, evidence_quote="I agree remote work can broaden hiring access"),
                CriterionEval(id="clear_counter", met=True, quality=0.9, evidence_quote="However, it should not always be the default"),
                CriterionEval(id="reasoned_basis", met=True, quality=0.9, evidence_quote="because weak onboarding can isolate distributed employees"),
                CriterionEval(id="civil_tone", met=True, quality=0.9, evidence_quote="I agree remote work can broaden hiring access"),
                CriterionEval(id="transfer_context", met=True, quality=0.9, evidence_quote="remote work can broaden hiring access"),
            ],
            next_focus="Try pressure.",
            pass_eligible=True,
        ),
    )

    assert result.pass_eligible is True


def test_gd_same_family_transfer_feedback_issues_corrected_motion_without_penalty():
    state = svc._new_state(
        "user-1",
        "session-gd-correct-transfer-feedback",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={
            "gd_topics": [
                "Should companies be allowed to use AI in hiring?",
                "Should remote work be the default?",
            ]
        },
    )
    state.update({
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "user_input": "I agree AI can improve consistency, but it can scale historical bias.",
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["transfer_context"],
            "blockers": ["minimum_gate:transfer_context"],
        },
        "tutor_turn_plan": {
            "verdict": "partial",
            "next_action": "rewrite",
            "allowed_praise": False,
        },
    })

    cleaned = svc._gd05_feedback_text(state)

    assert "does not count as transfer evidence" in cleaned
    assert 'Transfer task on "Should remote work be the default?"' in cleaned
    assert state["pending_prompt_attempt_type"] == "transfer"
    assert state["pending_gd_prompt_topic"] == "Should remote work be the default?"


def test_gd_take_floor_reconciles_browser_proven_entry_when_evaluator_omits_rows():
    state = svc._new_state(
        "user-1",
        "session-gd-take-floor-browser-proof",
        "gd_03_take_the_floor",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["messages"].append({
        "role": "assistant",
        "content": (
            "Someone just mentioned the benefits of remote work for hiring access. "
            "Link to that point, then add why it matters."
        ),
    })
    answer = (
        "Building on the point about hiring access, remote work lets a backend team recruit "
        "engineers with strong systems experience regardless of where they live. That matters "
        "because a wider talent pool improves coverage and resilience, but only if remote hires "
        "also receive visible ownership of design decisions."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_03_take_the_floor"), answer)
    omitted = PrepRubricEval(
        raw_score=0.0,
        criteria=[],
        required_missing=[
            "polite_entry_phrase",
            "links_prior_point",
            "adds_new_value",
            "assertive_not_rude",
        ],
        errors=["Does not provide clear evidence of claiming space assertively but politely."],
        next_focus="Assertiveness without rudeness",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, omitted)

    assert result.pass_eligible is True
    assert result.required_missing == []
    assert not any("assertive" in item.lower() for item in result.errors)
    assert "assertiveness without rudeness" not in result.next_focus.lower()


def test_gd_take_floor_feedback_uses_proven_entry_and_assigns_next_mini_discussion():
    state = svc._new_state(
        "user-1",
        "session-gd-take-floor-feedback",
        "gd_03_take_the_floor",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state.update({
        "user_input": (
            "Building on the point about hiring access, remote work broadens the talent pool. "
            "That matters because wider coverage improves incident resilience."
        ),
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "criteria": [
                {"id": "polite_entry_phrase", "met": True},
                {"id": "links_prior_point", "met": True},
                {"id": "adds_new_value", "met": True},
                {"id": "assertive_not_rude", "met": True},
            ],
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_fresh_independent",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "Great effort. Focus on using a signaling phrase.",
        state,
        "teach",
    )

    assert 'In your answer, you said "Building on the point about hiring access' in cleaned
    assert "linked to the prior point and added a substantive idea" in cleaned
    assert "remote onboarding weakens team culture" in cleaned
    assert "great effort" not in cleaned.lower()
    assert "focus on using a signaling phrase" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_gd_take_floor_does_not_pass_ask_only_or_generic_entry():
    state = svc._new_state(
        "user-1",
        "session-gd-take-floor-generic",
        "gd_03_take_the_floor",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_03_take_the_floor"),
        "Excuse me, can I speak now? I agree with that.",
    )
    omitted = PrepRubricEval(
        raw_score=0.0,
        criteria=[],
        required_missing=[
            "polite_entry_phrase",
            "links_prior_point",
            "adds_new_value",
        ],
        next_focus="Use a linked entry.",
        pass_eligible=False,
    )

    result = apply_caps(packet, omitted)

    assert result.pass_eligible is False
    assert any(
        blocker.startswith(("evaluator_incomplete:", "missing_required:"))
        for blocker in result.blockers
    )


def test_gd_build_on_feedback_quotes_extension_and_owns_transfer_task():
    state = svc._new_state(
        "user-1",
        "session-gd-build-on-feedback",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state.update({
        "user_input": (
            "Building on that point about hiring access, remote work broadens the talent pool. "
            "It also adds regional customer perspectives to design reviews."
        ),
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_transfer",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "Great job. Now. Suppose another person raises bias.",
        state,
        "teach",
    )

    assert 'In your answer, you said "Building on that point about hiring access' in cleaned
    assert "credited the prior point and extended it with a distinct implication" in cleaned
    assert "reduce unconscious bias" in cleaned
    assert "great job" not in cleaned.lower()
    assert "now. suppose" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "transfer"


def test_gd_build_on_transfer_changes_prior_point_with_motion():
    state = svc._new_state(
        "user-1",
        "session-gd-build-on-topic-transfer",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state.update({
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "user_input": (
            "Building on the fairness concern, AI screening needs cohort audits. "
            "I would add a human appeal path."
        ),
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_transfer",
            "allowed_praise": False,
        },
    })

    cleaned = svc._gd04_feedback_text(state)

    assert 'Transfer task on "Should remote work be the default?"' in cleaned
    assert "remote work broadens hiring access" in cleaned
    assert "data-driven screening" not in cleaned
    assert state["pending_gd_prompt_topic"] == "Should remote work be the default?"


def test_gd_build_on_reconciles_explicit_browser_proven_prior_credit():
    state = svc._new_state(
        "user-1",
        "session-gd-build-on-browser-proof",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    state["messages"].append({
        "role": "assistant",
        "content": (
            "A participant says data-driven screening can reduce unconscious bias. "
            "Credit that point and extend it."
        ),
    })
    answer = (
        "Building on your point that data-driven screening can reduce individual unconscious "
        "bias, I agree that consistent criteria can make early review more disciplined. I would "
        "add that the model can reproduce historical bias at scale, so teams need cohort audits "
        "and a human appeal path."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_04_build_on_others"), answer)
    raw = PrepRubricEval(
        raw_score=0.8,
        criteria=[
            CriterionEval(
                id="credits_prior_speaker",
                met=False,
                quality=0.6,
                reason="prior point was assumed rather than explicitly credited",
            ),
            CriterionEval(
                id="extends_idea",
                met=True,
                quality=0.85,
                evidence_quote=(
                    "I would add that the model can reproduce historical bias at scale, so teams "
                    "need cohort audits and a human appeal path."
                ),
            ),
            CriterionEval(
                id="topic_relevance",
                met=True,
                quality=0.85,
                evidence_quote="data-driven screening can reduce individual unconscious bias",
            ),
            CriterionEval(
                id="collaborative_tone",
                met=True,
                quality=0.85,
                evidence_quote=(
                    "Building on your point that data-driven screening can reduce individual "
                    "unconscious bias"
                ),
            ),
        ],
        required_missing=["credits_prior_speaker"],
        errors=["missing required rubric proof: credits_prior_speaker"],
        next_focus="Reference the prior speaker explicitly.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is True
    assert result.required_missing == []
    assert result.blockers == []
    assert not any("credits_prior_speaker" in item for item in result.errors)


def test_gd_build_on_does_not_credit_generic_agreement_without_prior_point():
    state = svc._new_state(
        "user-1",
        "session-gd-build-on-generic",
        "gd_04_build_on_others",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_04_build_on_others"),
        "I agree. AI hiring is useful and companies should use it.",
    )
    raw = PrepRubricEval(
        raw_score=0.4,
        criteria=[],
        required_missing=["credits_prior_speaker", "extends_idea", "topic_relevance"],
        next_focus="Credit and extend the prior point.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False


def test_gd_respectful_disagreement_reconciles_browser_proven_answer():
    state = svc._new_state(
        "user-1",
        "session-gd-disagree-browser-proof",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    state["messages"].append({
        "role": "assistant",
        "content": "A participant argues that companies should use AI in hiring because it reduces human bias.",
    })
    answer = (
        "I agree that standardized screening can reduce some inconsistent human judgments, and "
        "that is a real benefit. However, I do not think it proves AI reduces bias overall, because "
        "a model can encode historical patterns and apply them at much larger scale; companies "
        "should require cohort audits, human review, and an appeal path."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_05_disagree_respectfully"), answer)
    raw = PrepRubricEval(
        raw_score=0.85,
        criteria=[],
        required_missing=["acknowledges_valid_point", "clear_counter", "reasoned_basis"],
        errors=[
            "missing required rubric proof: acknowledges_valid_point, clear_counter, reasoned_basis"
        ],
        next_focus="Ensure every disagreement includes a reasoned counterpoint.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is True
    assert result.required_missing == []
    assert result.blockers == []
    assert {row.id for row in result.criteria if row.met} == {
        "acknowledges_valid_point",
        "clear_counter",
        "reasoned_basis",
        "civil_tone",
    }


@pytest.mark.parametrize(
    ("motion", "answer"),
    [
        (
            "Should companies use AI in hiring?",
            "I agree that AI screening can make hiring more consistent. However, automated models can encode historical bias, so recruiters need cohort audits and human review.",
        ),
        (
            "Should remote work be the default?",
            "I agree that remote work can broaden access to distributed teams. However, it should not be the default because weak onboarding can isolate new employees.",
        ),
        (
            "Should four-day workweeks become the standard?",
            "I agree that a four-day schedule can improve focus. However, a shorter workweek should not be standard because support coverage can suffer without staffing changes.",
        ),
        (
            "Should social-media platforms verify every user identity?",
            "I agree that social-media identity checks can reduce anonymous abuse. However, platforms should not require verification because vulnerable users may need pseudonymous accounts.",
        ),
        (
            "Should digital payments become the default?",
            "I agree that digital payments make transactions faster. However, cashless payment systems should not be the default because outages can exclude customers without reliable access.",
        ),
        (
            "Should universities require paid industry placements?",
            "I agree that universities can improve employability through placements. However, paid industry placements should not be required because rural students may have fewer accessible employers.",
        ),
    ],
)
def test_gd_respectful_disagreement_requires_and_accepts_robust_topic_grounding(
    motion,
    answer,
):
    state = svc._new_state(
        "user-1",
        "session-gd-disagree-grounded",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": [motion]},
    )
    result = apply_caps(
        build_evaluation_packet(state, svc.get_node("gd_05_disagree_respectfully"), answer),
        PrepRubricEval(
            raw_score=0.85,
            criteria=[],
            required_missing=["acknowledges_valid_point", "clear_counter", "reasoned_basis", "civil_tone"],
            next_focus="Ground the disagreement in the motion.",
            pass_eligible=False,
        ),
    )

    assert result.pass_eligible is True
    assert result.required_missing == []


def test_gd_respectful_disagreement_does_not_promote_structured_off_topic_answer():
    state = svc._new_state(
        "user-1",
        "session-gd-disagree-off-topic",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    answer = (
        "I agree that a rotating cafeteria menu can help students find more options. However, "
        "I do not think it should change weekly because suppliers need predictable orders and "
        "kitchen teams need stable preparation plans."
    )
    result = apply_caps(
        build_evaluation_packet(state, svc.get_node("gd_05_disagree_respectfully"), answer),
        PrepRubricEval(
            raw_score=0.85,
            criteria=[],
            required_missing=["acknowledges_valid_point", "clear_counter", "reasoned_basis", "civil_tone"],
            next_focus="Address the active motion.",
            pass_eligible=False,
        ),
    )

    assert result.pass_eligible is False


def test_gd_respectful_transfer_grounds_against_new_motion_not_composite_feedback():
    state = svc._new_state(
        "user-1",
        "session-gd-disagree-composite-transfer",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    parent_id = "session-gd-disagree-composite-transfer:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_05_disagree_respectfully",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should companies use AI in hiring?",
            "learner_answer": (
                "I agree AI screening can make hiring more consistent, but models can scale "
                "historical bias without cohort audits and human review."
            ),
        },
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "messages": [{
            "role": "assistant",
            "node_id": "gd_05_disagree_respectfully",
            "content": (
                "In your answer about AI hiring, you conceded a valid point. "
                'Transfer task on "Digital payments": a participant says the main benefit '
                "outweighs every implementation risk. Concede one benefit, then disagree."
            ),
        }],
    })
    answer = (
        "I agree that digital payments can reduce checkout friction and make transfers faster. "
        "However, cashless payment systems should not be the only default because outages and "
        "poor connectivity can exclude users, so services need a reliable cash fallback."
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_05_disagree_respectfully"),
        answer,
    )
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.85,
            criteria=[],
            required_missing=[
                "acknowledges_valid_point",
                "clear_counter",
                "reasoned_basis",
                "civil_tone",
                "transfer_context",
            ],
            next_focus="Ground the transfer in the new motion.",
            pass_eligible=False,
        ),
    )

    assert packet.active_topic == "Digital payments"
    assert result.pass_eligible is True
    assert result.required_missing == []


def test_gd_evidence_transfer_grounds_against_new_motion_not_composite_feedback():
    state = svc._new_state(
        "user-1",
        "session-gd-evidence-composite-transfer",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    parent_id = "session-gd-evidence-composite-transfer:core"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_02_support_with_evidence",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "active_topic": "Should companies use AI in hiring?",
            "learner_answer": "I support AI hiring because our pilot reduced review time by 20 percent.",
        },
        "active_prompt_attempt_type": "transfer",
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "messages": [{
            "role": "assistant",
            "node_id": "gd_02_support_with_evidence",
            "content": (
                "Your AI hiring evidence was specific. "
                'Transfer task on "Digital payments": support or oppose the motion with '
                "one concrete result and explain why it supports your stance."
            ),
        }],
    })
    answer = (
        "I support digital payments with a cash fallback because our checkout pilot reduced "
        "transaction time by 30 percent, which shows mobile payment flows can remove friction."
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_02_support_with_evidence"),
        answer,
    )
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.85,
            criteria=[],
            required_missing=[
                "clear_stance",
                "concrete_evidence",
                "topic_relevance",
                "evidence_link",
                "transfer_context",
            ],
            next_focus="Ground the evidence in the new motion.",
            pass_eligible=False,
        ),
    )

    assert packet.active_topic == "Digital payments"
    assert result.pass_eligible is True
    assert result.required_missing == []


def test_gd_respectful_disagreement_does_not_pass_personal_attack():
    state = svc._new_state(
        "user-1",
        "session-gd-disagree-attack",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("gd_05_disagree_respectfully"),
        "You are wrong and that idea is nonsense. AI is bad.",
    )
    raw = PrepRubricEval(
        raw_score=0.2,
        criteria=[],
        required_missing=["acknowledges_valid_point", "clear_counter", "reasoned_basis"],
        next_focus="Disagree with the idea, not the person.",
        pass_eligible=False,
    )

    assert apply_caps(packet, raw).pass_eligible is False


def test_gd_respectful_disagreement_feedback_is_anchored_and_assigns_transfer():
    state = svc._new_state(
        "user-1",
        "session-gd-disagree-feedback",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should companies use AI in hiring?"]},
    )
    state.update({
        "active_gd_prompt_topic": "Should companies use AI in hiring?",
        "user_input": (
            "I agree that consistent criteria can help. However, models can scale historical bias, "
            "so human review remains necessary."
        ),
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_transfer",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "Great job. Add the missing reasoning.",
        state,
        "teach",
    )

    assert 'In your answer, you said "I agree that consistent criteria can help' in cleaned
    assert "conceded a valid point, stated a clear counter, and gave a topic-based reason" in cleaned
    assert "shorter workweek improves focus and retention" in cleaned
    assert "great job" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "transfer"


def test_clear_gd_position_overrides_false_hedging_model_gap():
    state = svc._new_state(
        "user-1",
        "gd-stake-session",
        "gd_01_stake_position",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    answer = (
        "Remote work should be the default because it broadens hiring access and makes "
        "outcome-based performance the norm. Companies should manage security through "
        "managed devices, least-privilege access, incident playbooks, and monthly reviews."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_01_stake_position"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.65,
        criteria=[
            CriterionEval(id="clear_stance", met=True, quality=0.7, evidence_quote="Remote work should be the default"),
            CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="Remote work"),
            CriterionEval(id="low_hedging", met=False, quality=0.2, reason="answer uses but and caveats"),
            CriterionEval(id="concise_opening", met=True, quality=0.8, evidence_quote="Remote work should be the default"),
        ],
        required_missing=["low_hedging"],
        errors=["opening is hedged"],
        next_focus="Avoid but and state the position again.",
        on_task=True,
        english=True,
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert result.pass_eligible is True
    assert result.effective_score >= packet.pass_score
    assert result.required_missing == []
    assert all(row.met for row in result.criteria if row.id in {"clear_stance", "topic_relevance", "low_hedging"})
    assert "but" not in result.next_focus.lower()
    assert "hedg" not in result.next_focus.lower()


def test_genuinely_hedged_gd_position_is_not_overridden():
    state = svc._new_state(
        "user-1",
        "gd-hedged-session",
        "gd_01_stake_position",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    answer = "Maybe remote work should be the default, but it depends because both sides have valid points."
    packet = build_evaluation_packet(state, svc.get_node("gd_01_stake_position"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.55,
        criteria=[
            CriterionEval(id="clear_stance", met=False, quality=0.3, reason="position is conditional"),
            CriterionEval(id="topic_relevance", met=True, quality=0.8, evidence_quote="remote work"),
            CriterionEval(id="low_hedging", met=False, quality=0.1, reason="maybe and depends hedge the position"),
            CriterionEval(id="concise_opening", met=True, quality=0.8, evidence_quote=answer),
        ],
        required_missing=["clear_stance", "low_hedging"],
        next_focus="Choose one side without maybe or depends.",
        on_task=True,
        english=True,
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert result.pass_eligible is False
    assert {"clear_stance", "low_hedging"}.issubset(result.required_missing)


def test_repeated_incomplete_evaluation_routes_to_explicit_unscored_retry(monkeypatch):
    from app.ai.calls import PrepEvaluationRetryRequired
    from app.graph import build as graph_build
    from app.graph.nodes import evaluate as eval_node

    async def incomplete_prep_eval(*_args, **_kwargs):
        raise PrepEvaluationRetryRequired(["topic_relevance"])

    monkeypatch.setattr(eval_node, "evaluate_prep_answer", incomplete_prep_eval)
    graph_build.get_graph.cache_clear()
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    answer = (
        "I support AI in campus placements because our campus pilot reduced placement "
        "turnaround from 10 days to 6."
    )
    state.update({
        "turn_count": 1,
        "user_input": answer,
        "current_mastery": 0.42,
        "attempts": 3,
        "session_attempts": 2,
        "last_eval_score": 0.78,
        "last_clean_pass_score": 0.78,
    })

    try:
        updates = _run(graph_build.get_graph().ainvoke(state))
    finally:
        graph_build.get_graph.cache_clear()

    assert updates["evaluation_retry_required"] is True
    assert updates["evaluation_integrity_failure"] == {
        "code": "required_criteria_omitted",
        "criterion_ids": ["topic_relevance"],
    }
    assert updates["last_route"] == "evaluation_retry"
    assert updates["current_mastery"] == 0.42
    assert updates["attempts"] == 3
    assert updates["session_attempts"] == 2
    assert updates["last_eval_score"] == 0.78
    assert updates["last_clean_pass_score"] == 0.78


def test_evaluation_retry_turn_is_visible_durable_and_has_no_learning_side_effects(monkeypatch, store):
    retry_text = (
        "I couldn't review that answer reliably, so I haven't counted it. "
        "Please send the same answer once more."
    )

    class RetryGraph:
        async def ainvoke(self, _state):
            return {
                "evaluation_retry_required": True,
                "evaluation_integrity_failure": {
                    "code": "required_criteria_omitted",
                    "criterion_ids": ["topic_relevance"],
                },
                "last_route": "evaluation_retry",
                "pending": None,
                "pending_game": None,
                "pending_prompt_attempt_type": "pressure",
            }

    monkeypatch.setattr(svc, "get_graph", lambda: RetryGraph())
    state = svc._new_state(
        "user-1",
        "session-eval-retry",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    state.update({
        "messages": [{"role": "assistant", "content": "Give your stance and evidence."}],
        "turn_count": 1,
        "opening_streamed": True,
        "current_mastery": 0.42,
        "attempts": 3,
        "session_attempts": 2,
        "clean_streak": 1,
        "readiness_score": 0.65,
        "meaningful_attempts": 2,
        "independent_passes": 1,
        "last_gap": "existing learner gap",
        "last_eval_score": 0.78,
        "last_clean_pass_score": 0.78,
        "active_prompt_attempt_type": "transfer",
        "session_version": 7,
        "session_learning_delta": {
            "strengths": ["existing strength"],
            "active_gaps": ["existing learner gap"],
            "repeated_issue_counts": {"existing learner gap": 2},
            "growth_signals": [],
            "resolved_candidates": [],
            "latest_evidence_quotes": ["existing evidence"],
        },
    })
    store.mastery[("user-1", "gd_02_support_with_evidence")] = {"mastery": 0.42, "attempts": 3}
    svc.SessionStore[state["session_id"]] = state
    answer = (
        "I support AI in campus placements because our campus pilot reduced placement "
        "turnaround from 10 days to 6."
    )

    items = _run(_collect_async(svc.run_turn(state["session_id"], answer, client_turn_id="turn-retry")))

    assert items == [retry_text]
    assert not any(term in retry_text.lower() for term in ("evaluator", "model", "criterion", "internal"))
    assert state["messages"][-2]["role"] == "user"
    assert state["messages"][-2]["content"] == answer
    assert state["messages"][-1] == {
        "role": "assistant",
        "content": retry_text,
        "node_id": "gd_02_support_with_evidence",
        "turn_id": "turn-retry",
        "message_kind": "evaluation_retry",
    }
    assert state["last_turn_status"] == "completed"
    assert state["active_turn_status"] == "completed"
    assert state["input_allowed"] is True
    assert state["block_reason"] is None
    assert state["session_version"] == 8
    assert state["current_mastery"] == 0.42
    assert state["attempts"] == 3
    assert state["session_attempts"] == 2
    assert state["clean_streak"] == 1
    assert state["readiness_score"] == 0.65
    assert state["meaningful_attempts"] == 2
    assert state["independent_passes"] == 1
    assert state["last_gap"] == "existing learner gap"
    assert state["last_eval_score"] == 0.78
    assert state["last_clean_pass_score"] == 0.78
    assert state["pending_prompt_attempt_type"] is None
    assert state["active_prompt_attempt_type"] == "transfer"
    assert state["session_learning_delta"] == {
        "strengths": ["existing strength"],
        "active_gaps": ["existing learner gap"],
        "repeated_issue_counts": {"existing learner gap": 2},
        "growth_signals": [],
        "resolved_candidates": [],
        "latest_evidence_quotes": ["existing evidence"],
    }
    assert store.mastery[("user-1", "gd_02_support_with_evidence")] == {"mastery": 0.42, "attempts": 3}
    assert store.turn_evaluations == []
    assert store.learning_events == []
    assert store.learner_skill_profiles == {}

    persisted = store.session_runtime[state["session_id"]]
    restored = svc._hydrate_runtime_state(persisted)
    assert restored["messages"][-2:] == state["messages"][-2:]
    assert restored["evaluation_retry_required"] is True
    assert restored["last_turn_status"] == "completed"
    assert restored["input_allowed"] is True
    assert restored["session_version"] == 8
    assert restored["pending_prompt_attempt_type"] is None
    assert restored["active_prompt_attempt_type"] == "transfer"


def test_bridge_node_targets_missing_star_result_criterion():
    from app.graph.nodes.bridge import bridge_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    state["last_eval_score"] = 0.54
    state["last_rubric_result"] = {
        "required_missing": ["result"],
        "blockers": ["missing_required:result"],
        "next_focus": "Add the result or measurable impact.",
        "criteria": [
            {"id": "action", "met": True, "quality": 0.7, "evidence_quote": "added alerts"},
            {"id": "result", "met": False, "quality": 0.1, "reason": "No outcome named."},
        ],
    }

    updates = _run(bridge_node(state))

    assert updates["pending_game"]["id"] == "int_04_star_behavioral_bx4"
    assert "outcome" in updates["pending_game"]["context"].lower()
    assert updates["active_prompt_attempt_type"] == "scaffolded"


def test_bridge_node_targets_weakness_progress_evidence_criterion():
    from app.graph.nodes.bridge import bridge_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    state["last_eval_score"] = 0.58
    state["last_rubric_result"] = {
        "required_missing": ["progress_evidence"],
        "blockers": ["missing_required:progress_evidence"],
        "next_focus": "Add a recent sign it is improving.",
        "criteria": [
            {"id": "real_weakness", "met": True, "quality": 0.7, "evidence_quote": "over-explain"},
            {"id": "mitigation_habit", "met": True, "quality": 0.7, "evidence_quote": "start with criteria"},
            {"id": "progress_evidence", "met": False, "quality": 0.1, "reason": "No progress signal."},
        ],
    }

    updates = _run(bridge_node(state))

    assert updates["pending_game"]["id"] == "int_03_weakness_framing_bx4"
    assert "improving" in updates["pending_game"]["sentence"].lower()


def test_late_session_core_pass_routes_to_real_transfer_instead_of_teach_loop():
    from app.graph.route import route_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
    )
    state.update({
        "last_eval_score": 0.85,
        "session_attempts": 19,
        "clean_streak": 0,
        "independent_passes": 7,
        "transfer_passes": 0,
        "pressure_passes": 0,
        "last_diagnosis": {"on_task": True, "english": True},
        "last_rubric_result": {
            "pass_eligible": True,
            "attempt_type": "independent",
            "required_missing": [],
            "blockers": [],
        },
    })

    assert route_node(state) == "challenge"


def test_challenge_node_marks_next_answer_as_transfer_attempt():
    from app.graph.nodes.challenge import challenge_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    state["independent_passes"] = 2
    state["tutor_turn_plan"] = {
        "verdict": "independent_pass",
        "next_action": "request_transfer",
        "focus": "apply the skill in a different context",
    }

    updates = _run(challenge_node(state))

    assert updates["last_route"] == "challenge"
    assert updates["pending_prompt_attempt_type"] == "transfer"
    assert "active_prompt_attempt_type" not in updates
    assert "complete harder variant" in updates["pending"].prompt.lower()


def test_int01_challenge_projects_current_transfer_pass_to_pending_pressure():
    from app.graph.nodes.challenge import challenge_node

    state = svc._new_state(
        "user-1",
        "session-int01-transfer-pass",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state.update({
        "independent_passes": 2,
        "transfer_passes": 0,
        "core_qualified": True,
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_pressure",
            "focus": "defend the qualified core pitch",
        },
    })
    parent_id = "session-int01-transfer-pass:turn-core:int_01_elevator_pitch"
    state.update({
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_01_elevator_pitch",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": "I am a backend engineer who improved payment reliability.",
        },
    })

    updates = _run(challenge_node(state))

    assert updates["pending_prompt_attempt_type"] == "pressure"
    assert "active_prompt_attempt_type" not in updates
    assert "pressure" in updates["pending"].prompt.lower()


def test_challenge_node_honors_fresh_independent_tutor_plan():
    from app.graph.nodes.challenge import challenge_node

    state = svc._new_state(
        "user-1",
        "session-why-company-challenge",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
        career_context={
            "primary_role": "Backend Software Engineer",
            "target_roles": ["Backend Software Engineer", "Platform Engineer"],
        },
    )
    state.update({
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "independent",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_fresh_independent",
            "focus": "demonstrate the same skill with a different learner-owned example",
        },
    })

    updates = _run(challenge_node(state))

    assert updates["pending_prompt_attempt_type"] == "independent"
    assert "fresh independent demonstration" in updates["pending"].prompt.lower()
    assert "harder transfer" not in updates["pending"].prompt.lower()
    assert "Platform Engineer" not in updates["pending"].prompt


def test_challenge_node_cannot_stage_pressure_without_authenticated_core():
    from app.graph.nodes.challenge import challenge_node

    state = svc._new_state(
        "user-1",
        "session-invalid-pressure-challenge",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
    )
    state.update({
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_pressure",
            "focus": "defend the answer",
        },
    })

    updates = _run(challenge_node(state))

    assert updates["pending_prompt_attempt_type"] == "independent"
    assert "fresh independent demonstration" in updates["pending"].prompt.lower()


def test_challenge_node_missing_plan_cannot_infer_pressure_from_counter_alone():
    from app.graph.nodes.challenge import challenge_node

    state = svc._new_state(
        "user-1",
        "session-missing-plan-pressure-challenge",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
    )
    state.update({
        "transfer_passes": 1,
        "tutor_turn_plan": None,
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
    })

    updates = _run(challenge_node(state))

    assert updates["pending_prompt_attempt_type"] == "independent"
    assert "fresh independent demonstration" in updates["pending"].prompt.lower()


def test_challenge_node_malformed_plan_cannot_infer_transfer_from_counters():
    from app.graph.nodes.challenge import challenge_node

    state = svc._new_state(
        "user-1",
        "session-malformed-plan-transfer-challenge",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
    )
    state.update({
        "independent_passes": 2,
        "transfer_passes": 0,
        "tutor_turn_plan": {"verdict": "independent_pass", "next_action": ""},
    })

    updates = _run(challenge_node(state))

    assert updates["pending_prompt_attempt_type"] == "independent"
    assert "fresh independent demonstration" in updates["pending"].prompt.lower()


def test_int01_qualified_reattempt_opens_with_pressure_not_initial_pitch(monkeypatch, store):
    async def unexpected_model_call(_spec):
        raise AssertionError("qualified int_01 reattempt should use the deterministic pressure task")
        yield "unreachable"

    monkeypatch.setattr(svc, "stream_generation", unexpected_model_call)
    state = svc._new_state(
        "user-1",
        "session-int01-qualified-reattempt",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state.update({
        "reattempt": True,
        "readiness_score": 0.8,
        "independent_passes": 2,
        "transfer_passes": 1,
        "pressure_passes": 0,
    })
    parent_id = "session-int01-qualified-reattempt:turn-core:int_01_elevator_pitch"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_01_elevator_pitch",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": "I am a backend engineer who improved payment reliability.",
        },
    })
    svc.SessionStore[state["session_id"]] = state

    opening = "".join(_run(_collect_async(svc.stream_opening(state["session_id"]))))

    assert "skeptical interviewer" in opening.lower()
    assert "repeat or scale" in opening.lower()
    assert "craft your 30-second pitch" not in opening.lower()
    assert state["active_prompt_attempt_type"] == "pressure"
    assert state["pending_prompt_attempt_type"] is None
    assert state["opening_streamed"] is True


def test_int01_reattempt_without_authenticated_core_cannot_open_with_pressure():
    state = svc._new_state(
        "user-1",
        "session-int01-invalid-reattempt-parent",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state.update({
        "reattempt": True,
        "independent_passes": 2,
        "transfer_passes": 1,
        "pressure_passes": 0,
        "core_qualified": True,
        "core_qualification_turn_id": None,
        "core_qualification_evidence": None,
    })

    opening = svc._int01_reattempt_opening_text(state)

    assert "introduce yourself again" in opening.lower()
    assert "skeptical interviewer" not in opening.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_why_company_stream_opening_is_deterministic_and_committed(monkeypatch, store):
    async def unexpected_model_call(_spec):
        raise AssertionError("int_05 opening should not invent a company through the model")
        yield "unreachable"

    monkeypatch.setattr(svc, "stream_generation", unexpected_model_call)
    state = svc._new_state(
        "user-1",
        "session-why-company-opening-stream",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
        career_context={
            "primary_role": "Backend Software Engineer",
            "target_roles": ["Backend Software Engineer", "Platform Engineer"],
        },
    )
    svc.SessionStore[state["session_id"]] = state

    opening = "".join(_run(_collect_async(svc.stream_opening(state["session_id"]))))

    assert "choose a company" in opening.lower()
    assert "Backend Software Engineer" in opening
    assert "this company" not in opening.lower()
    assert state["opening_streamed"] is True
    assert state["messages"][-1]["content"] == opening
    assert state["committed_openings"]["initial:int_05_why_this_role"] == opening


def test_gd_challenge_attempt_selection_and_text_are_unchanged_except_pending_marker():
    from app.graph.nodes.challenge import challenge_node

    state = svc._new_state(
        "user-1",
        "session-gd-challenge-non-regression",
        "gd_01_stake_position",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["AI in campus placements"]},
    )
    state.update({
        "transfer_passes": 0,
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_transfer",
            "focus": "apply the skill on a different motion",
        },
    })

    updates = _run(challenge_node(state))

    assert updates["pending_prompt_attempt_type"] == "transfer"
    assert "active_prompt_attempt_type" not in updates
    assert "complete harder variant" in updates["pending"].prompt.lower()


def test_compiled_graph_preserves_career_stage_and_parent_channels(monkeypatch):
    from app.graph import build as graph_build

    seen = {}

    async def fake_evaluate(state):
        seen["evaluate"] = {
            key: state.get(key)
            for key in (
                "independent_passes",
                "transfer_passes",
                "pressure_passes",
                "core_qualified",
                "core_qualification_turn_id",
                "core_qualification_evidence",
            )
        }
        return {
            "last_eval_score": 0.86,
            "last_clean_pass_score": 0.86,
            "last_diagnosis": {"on_task": True, "english": True},
            "last_rubric_result": {
                "pass_eligible": True,
                "attempt_type": "independent",
                "required_missing": [],
                "blockers": [],
            },
        }

    async def fake_challenge(state):
        seen["challenge"] = {
            "independent_passes": state.get("independent_passes"),
            "transfer_passes": state.get("transfer_passes"),
            "pressure_passes": state.get("pressure_passes"),
        }
        packet = build_evaluation_packet(
            state,
            svc.get_node("int_03_weakness_framing"),
            "I would defend the rollout with the measured failure rate.",
        )
        seen["packet"] = packet
        return {
            "pending": None,
            "last_route": "challenge",
            "pending_prompt_attempt_type": "pressure",
        }

    monkeypatch.setattr(graph_build, "evaluate_node", fake_evaluate)
    monkeypatch.setattr(graph_build, "challenge_node", fake_challenge)
    graph_build.get_graph.cache_clear()
    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    parent_id = "session-old:turn-core-2:int_03_weakness_framing"
    state.update({
        "turn_count": 2,
        "independent_passes": 4,
        "transfer_passes": 0,
        "pressure_passes": 0,
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_03_weakness_framing",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": (
                "My weakness was rushing rollouts; I now use phased pilots and decision gates."
            ),
        },
        "active_prompt_attempt_type": "pressure",
    })

    _run(graph_build.get_graph().ainvoke(state))
    graph_build.get_graph.cache_clear()

    assert seen["evaluate"]["independent_passes"] == 4
    assert seen["evaluate"]["core_qualification_turn_id"] == parent_id
    assert seen["challenge"]["transfer_passes"] == 0
    assert seen["packet"].core_qualified is True
    assert [row["id"] for row in seen["packet"].criteria] == [
        "pressure_response", "evidence_defense", "core_consistency"
    ]


def test_why_company_transfer_keeps_node_rubric_and_adds_only_transfer_context():
    state = svc._new_state(
        "user-1",
        "session-why-company-transfer-rubric",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    parent_id = "session-why-company-transfer-rubric:turn-core:int_05_why_this_role"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_05_why_this_role",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
        },
        "active_prompt_attempt_type": "transfer",
    })

    packet = build_evaluation_packet(
        state,
        svc.get_node("int_05_why_this_role"),
        "Stripe's billing platform matches my idempotent payment experience.",
    )

    assert [row["id"] for row in packet.criteria] == [
        "company_specific_fact",
        "personal_motivation_link",
        "role_relevance",
        "non_generic",
        "transfer_context",
    ]
    assert "corrective_application" not in {row["id"] for row in packet.criteria}
    assert "transfer_result" not in {row["id"] for row in packet.criteria}


def test_partial_transfer_revision_keeps_transfer_attempt_ownership():
    state = {
        "active_prompt_attempt_type": None,
        "pending_prompt_attempt_type": None,
    }

    svc._stage_pending_prompt_attempt_type(state, "transfer")

    assert state["active_prompt_attempt_type"] == "transfer"
    assert state["pending_prompt_attempt_type"] == "transfer"

    svc._commit_pending_prompt_attempt_type(state)

    assert state["active_prompt_attempt_type"] == "transfer"
    assert state["pending_prompt_attempt_type"] is None


def test_bridge_selector_uses_missing_gd_evidence_gap_within_target_band():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="stance-standard",
            type="multiple_choice",
            sentence="Which opening commits to a side?",
            hint="clear side first",
            context="Practises taking a clear stance.",
            answer_key="I support it with one condition.",
            options=[
                "I support it with one condition.",
                "It depends on many things.",
            ],
            band="standard",
        ),
        BridgeExercise(
            id="evidence-standard",
            type="multiple_choice",
            sentence="Which reply adds concrete evidence to the GD point?",
            hint="look for an example, fact, or metric",
            context="Targets the concrete evidence gap instead of repeating a stance.",
            answer_key="For instance, the pilot cut turnaround time by 20%.",
            options=[
                "For instance, the pilot cut turnaround time by 20%.",
                "I strongly believe this is correct.",
            ],
            band="standard",
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=[],
        score=0.55,
        gap_context={
            "required_missing": ["concrete_evidence"],
            "blockers": ["missing_required:concrete_evidence"],
            "next_focus": "Add one concrete example or data-backed reason.",
        },
    )

    assert selected.id == "evidence-standard"


def test_bridge_selector_skips_served_targeted_exercise_before_fallback():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="evidence-standard-a",
            type="fill_blank",
            sentence="For instance, the pilot cut ___ by 20%.",
            hint="a metric",
            context="Targets the concrete evidence gap.",
            answer_key="turnaround time",
            band="standard",
        ),
        BridgeExercise(
            id="stance-standard",
            type="fill_blank",
            sentence="I ___ this policy.",
            hint="commit to a side",
            context="Targets a clear stance.",
            answer_key="support",
            band="standard",
        ),
        BridgeExercise(
            id="evidence-standard-b",
            type="multiple_choice",
            sentence="Which sentence adds evidence?",
            hint="pick the one with data",
            context="A second concrete evidence drill.",
            answer_key="A trial across 300 users reduced wait time.",
            options=[
                "A trial across 300 users reduced wait time.",
                "I feel this is better.",
            ],
            band="standard",
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=["evidence-standard-a"],
        score=0.55,
        gap_context={"required_missing": ["concrete_evidence"]},
    )

    assert selected.id == "evidence-standard-b"


def test_bridge_selector_prefers_explicit_failed_criterion_before_band_distance():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="generic-standard",
            type="fill_blank",
            sentence="I ___ the project plan.",
            hint="name an action",
            context="A generic action drill.",
            answer_key="updated",
            band="standard",
            criterion_ids=["actions"],
        ),
        BridgeExercise(
            id="result-stretch",
            type="spoken",
            sentence="State what changed because of your action.",
            hint="give the observable outcome",
            context="Repairs the missing STAR result.",
            answer_key="Expected element: one observable result caused by the learner's action.",
            band="stretch",
            criterion_ids=["result"],
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=[],
        score=0.55,
        gap_context={"required_missing": ["result"]},
    )

    assert selected.id == "result-stretch"


def test_bridge_selector_without_gap_context_preserves_severity_order():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="first-standard",
            type="fill_blank",
            sentence="I ___ this policy.",
            hint="commit to a side",
            context="First standard exercise.",
            answer_key="support",
            band="standard",
        ),
        BridgeExercise(
            id="second-standard",
            type="fill_blank",
            sentence="For instance, the pilot cut ___ by 20%.",
            hint="a metric",
            context="Second standard exercise.",
            answer_key="turnaround time",
            band="standard",
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=[],
        score=0.55,
    )

    assert selected.id == "first-standard"


def test_bridge_selector_preserves_foundational_scaffold_for_very_weak_answer():
    from app.content.schema import BridgeExercise

    exercises = [
        BridgeExercise(
            id="foundation-stem",
            type="fill_blank",
            sentence="I ___ this policy.",
            hint="commit to a side",
            context="Foundational stance stem.",
            answer_key="support",
            band="foundational",
        ),
        BridgeExercise(
            id="evidence-standard",
            type="fill_blank",
            sentence="For instance, the pilot cut ___ by 20%.",
            hint="a metric",
            context="Targets the concrete evidence gap.",
            answer_key="turnaround time",
            band="standard",
        ),
    ]

    selected = select_bridge_exercise(
        exercises,
        bridge_attempts=0,
        served_ids=[],
        score=0.1,
        gap_context={"required_missing": ["concrete_evidence"]},
    )

    assert selected.id == "foundation-stem"


def test_bridge_selector_returns_none_instead_of_reusing_served_exercises():
    from app.content.schema import BridgeExercise

    exercise = BridgeExercise(
        id="already-served",
        type="fill_blank",
        sentence="I ___ this policy.",
        hint="commit to a side",
        context="Foundational stance stem.",
        answer_key="support",
        band="foundational",
        criterion_ids=["clear_stance"],
    )

    assert select_bridge_exercise(
        [exercise],
        bridge_attempts=1,
        served_ids=[exercise.id],
        score=0.3,
        gap_context={"required_missing": ["clear_stance"]},
    ) is None


def test_bridge_selector_returns_none_when_only_unsafe_band_remains():
    from app.content.schema import BridgeExercise

    stretch = BridgeExercise(
        id="result-stretch-only",
        type="spoken",
        sentence="Give the complete STAR story under pressure.",
        hint="include all four beats",
        context="A stretch production task.",
        answer_key="Expected elements: situation, task, action, result.",
        band="stretch",
        criterion_ids=["result"],
    )

    assert select_bridge_exercise(
        [stretch],
        bridge_attempts=0,
        served_ids=[],
        score=0.1,
        gap_context={"required_missing": ["result"]},
    ) is None


def test_bridge_node_exhausted_authored_pool_generates_fresh_scaffold():
    from app.graph.nodes.bridge import bridge_node

    state = svc._new_state(
        "user-1",
        "session-exhausted-bridges",
        "int_02_strength_with_evidence",
        [{"role": "user", "content": "I stay calm under pressure."}],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    node = svc.get_node("int_02_strength_with_evidence")
    state["served_bridge_ids"] = [exercise.id for exercise in node.bridge_exercises]
    state["bridge_attempts"] = 1
    state["last_diagnosis"] = {"next_focus": "Add learner-owned evidence."}

    update = _run(bridge_node(state))

    assert update["pending"].kind == "bridge"
    assert "pending_game" not in update
    assert update["last_route"] == "bridge"
    assert update["bridge_attempts"] == 2
    assert update["active_prompt_attempt_type"] == "scaffolded"


@pytest.mark.parametrize(
    ("node_id", "criterion_id", "expected_exercise"),
    [
        ("int_06_own_a_failure", "impact", "int_06_own_a_failure_bx3"),
        ("int_06_own_a_failure", "response_action", "int_06_own_a_failure_bx3"),
        ("int_11_salary_negotiation", "collaborative_flexibility", "int_11_salary_negotiation_bx3"),
    ],
)
def test_authored_bridge_pool_covers_each_specialized_interview_gap(
    node_id,
    criterion_id,
    expected_exercise,
):
    node = svc.get_node(node_id)

    selected = select_bridge_exercise(
        node.bridge_exercises,
        bridge_attempts=0,
        served_ids=[],
        score=0.55,
        gap_context={"required_missing": [criterion_id]},
    )

    assert selected is not None
    assert selected.id == expected_exercise


def test_interview_pitch_complete_evidence_repairs_omitted_evaluator_rows_without_deficit_focus():
    answer = (
        "I’m a backend software engineer focused on reliable payment and event-driven systems. "
        "My strength is turning failure-prone workflows into observable, resilient services; in a recent "
        "payments migration, I used idempotency and staged rollout controls to cut duplicate writes by 96% "
        "and reduce status latency from 18 seconds to 4. I’m now looking to own larger distributed systems "
        "where reliability improvements directly protect revenue and customer trust."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.80,
        criteria=[
            CriterionEval(id="pitch_structure", met=False, quality=0.2, reason="missing structure"),
            CriterionEval(id="future_goal", met=False, quality=0.2, reason="missing future goal"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Add a future goal.",
        pass_eligible=True,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}
    required_ids = {str(item["id"]) for item in packet.criteria if item.get("required")}

    assert required_ids
    assert result.required_missing == []
    assert all(rows[criterion_id].met for criterion_id in required_ids)
    assert result.blockers == []
    assert result.effective_score == 0.80
    assert result.pass_eligible is True
    assert result.mastery_eligible is False
    assert not any(
        phrase in result.next_focus.lower()
        for phrase in ("measurable impact", "sharper role fit", "rewrite", "another role")
    )
    assert any(phrase in result.next_focus.lower() for phrase in ("pressure", "delivery", "transfer"))


def test_interview_pitch_live_transfer_inflections_reconcile_as_concrete_proof():
    answer = (
        "I’m a backend software engineer who also focuses on operational clarity for "
        "cross-functional teams. In a separate incident-response initiative, I redesigned "
        "alert ownership and runbook handoffs, cutting mean time to acknowledge from 12 "
        "minutes to 3 and reducing repeat escalations by 40%. I’m looking to lead platform "
        "reliability work where engineering signals are understandable to product and support teams."
    )
    state = svc._new_state(
        "user-1",
        "session-live-transfer",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.8,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.8, evidence_quote="backend software engineer"),
            CriterionEval(id="specific_detail", met=False, quality=0.2, reason="detail not recognized"),
            CriterionEval(id="pitch_structure", met=False, quality=0.2, reason="proof not recognized"),
            CriterionEval(id="future_goal", met=True, quality=0.8, evidence_quote="looking to lead platform reliability"),
        ],
        required_missing=["specific_detail", "pitch_structure"],
        errors=["missing required rubric proof: specific_detail, pitch_structure"],
        next_focus="Add a concrete result.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["specific_detail"].met is True
    assert rows["pitch_structure"].met is True
    assert result.required_missing == []
    assert result.blockers == []
    assert result.effective_score == 0.8
    assert result.pass_eligible is True
    assert result.mastery_eligible is False


@pytest.mark.parametrize(
    "answer",
    [
        "I redesigned the incident handoff, cutting response time by 40%.",
        "I am redesigning the incident handoff and reducing repeat escalations by 40%.",
        "I implemented a FastAPI payment API, preventing duplicate transactions.",
        "I am building a FastAPI payment API and improving latency by 20%.",
        "I resolved a checkout incident, reducing failures from 8% to 2%.",
    ],
)
def test_pitch_detail_gate_recognizes_natural_action_inflections(answer):
    from app.services.rubric_engine import _has_concrete_pitch_detail

    assert _has_concrete_pitch_detail(answer) is True


def test_interview_pitch_future_goal_evidence_is_reconciled_before_caps():
    answer = (
        "I'm a backend engineer focused on reliable APIs, payment flows, and production debugging. "
        "In a payment service, I traced retry/idempotency gaps and added safer transaction logging. "
        "My next goal is to own larger distributed systems and mentor engineers on operational discipline."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.86,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.8, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.8, evidence_quote="payment service"),
            CriterionEval(id="pitch_structure", met=False, quality=0.2, evidence_quote="", reason="missing direction"),
            CriterionEval(id="future_goal", met=False, quality=0.2, evidence_quote="", reason="missing future goal"),
        ],
        required_missing=["pitch_structure"],
        errors=["missing required rubric proof: pitch_structure"],
        next_focus="add a clear future goal",
        pass_eligible=True,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["future_goal"].met is True
    assert rows["pitch_structure"].met is True
    assert result.required_missing == []
    assert result.effective_score >= packet.pass_score
    assert result.pass_eligible is True
    assert result.mastery_eligible is False
    assert "future goal" not in result.next_focus.lower()


def test_interview_weakness_shape_evidence_is_reconciled_before_caps():
    answer = (
        "A weakness I have been working on is holding onto incident ownership too long "
        "before escalating, not ignoring protocol or avoiding shared ownership. During a "
        "payment-retry outage, I spent about 40 minutes "
        "debugging alone because I wanted to solve it myself. In the retrospective I "
        "proposed a 15-minute escalation rule and paired incident roles, and I started "
        "explicitly naming when I needed another perspective. Across the next three "
        "incidents, median escalation time fell from 35 minutes to 11. I still own incidents "
        "safely, but I now escalate within 15 minutes when a failure crosses team boundaries."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.78,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.6, evidence_quote="holding onto incident ownership"),
            CriterionEval(id="mitigation_habit", met=False, quality=0.2, reason="habit is too implicit"),
            CriterionEval(id="progress_evidence", met=False, quality=0.2, reason="progress evidence is not explicit"),
            CriterionEval(
                id="non_self_sabotage",
                met=False,
                quality=0.2,
                reason="The weakness affects a core role requirement for incident ownership.",
            ),
        ],
        required_missing=["mitigation_habit", "progress_evidence", "non_self_sabotage"],
        errors=[
            "missing required rubric proof: mitigation_habit, progress_evidence, non_self_sabotage"
        ],
        next_focus="Add the corrective habit and concrete progress evidence.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["real_weakness"].met is True
    assert rows["mitigation_habit"].met is True
    assert rows["progress_evidence"].met is True
    assert rows["non_self_sabotage"].met is True
    assert "escalation rule" in rows["mitigation_habit"].evidence_quote
    assert "fell from 35 minutes to 11" in rows["progress_evidence"].evidence_quote
    assert result.required_missing == []
    assert result.effective_score >= packet.pass_score
    assert result.pass_eligible is True
    assert result.mastery_eligible is False
    assert "progress evidence" not in result.next_focus.lower()
    assert "three-part weakness answer" not in result.next_focus.lower()
    assert "pressure-test" in result.next_focus.lower()


def test_interview_weakness_progress_accepts_owned_prevention_outcome():
    from app.services.rubric_engine import (
        _has_concrete_weakness_progress,
        _weakness_progress_evidence,
    )

    answer = (
        "I used to wait too long before escalating payment incidents. I now use a "
        "15-minute escalation rule and name the second incident owner immediately. "
        "During the last two incidents, I escalated within 15 minutes and there was "
        "no additional customer impact."
    )

    assert _has_concrete_weakness_progress(answer) is True
    assert "no additional customer impact" in _weakness_progress_evidence(answer).lower()


def test_interview_weakness_progress_accepts_live_restored_service_outcome():
    from app.services.rubric_engine import (
        _has_concrete_weakness_progress,
        _weakness_progress_evidence,
    )

    answer = (
        "One weakness I have been working on is escalating production risks too late. "
        "During a payment-service migration, I spent too long debugging an intermittent "
        "timeout alone, which delayed rollback by about 40 minutes. Since then I use a "
        "20-minute escalation rule and ask an owner to challenge my incident hypothesis. "
        "In the last two incidents, we involved the right database engineer within 15 "
        "minutes and restored service without extending the customer impact."
    )

    assert _has_concrete_weakness_progress(answer) is True
    assert "restored service" in _weakness_progress_evidence(answer).lower()


def test_interview_weakness_progress_composes_adjacent_event_sentences():
    from app.services.rubric_engine import (
        _has_concrete_weakness_progress,
        _weakness_progress_evidence,
    )

    answer = (
        "I used to wait too long before escalating payment incidents. I now use a "
        "15-minute escalation rule. During the last two payment incidents, I escalated "
        "within 15 minutes. There was no additional customer impact."
    )

    assert _has_concrete_weakness_progress(answer) is True
    assert "no additional customer impact" in _weakness_progress_evidence(answer).lower()


def test_interview_weakness_checklist_result_repairs_contradictory_model_evidence():
    answer = (
        "A weakness I am managing is missing migration edge cases when I am moving fast. "
        "I now use a pre-deploy checklist covering lock risk, regional timing, rollback commands, "
        "alert ownership, and reviewer sign-off. Since adopting it, two schema changes shipped "
        "without checkout errors, and rollback readiness improved from ad hoc notes to a tested "
        "command runbook."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.79,
        criteria=[
            CriterionEval(id="real_weakness", met=True, evidence_quote="missing migration edge cases"),
            CriterionEval(id="mitigation_habit", met=True, evidence_quote="pre-deploy checklist"),
            CriterionEval(id="progress_evidence", met=False, reason="no completed result"),
            CriterionEval(id="non_self_sabotage", met=False, reason="the framing boundary is unclear"),
        ],
        required_missing=["progress_evidence", "non_self_sabotage"],
        errors=["missing required rubric proof: progress_evidence, non_self_sabotage"],
        strengths=["The checklist already improved schema delivery and rollback readiness."],
        next_focus="Frame the weakness honestly without disqualifying yourself.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["progress_evidence"].met is True
    assert "rollback readiness improved" in rows["progress_evidence"].evidence_quote
    assert rows["progress_evidence"].evidence_quote in answer
    assert rows["non_self_sabotage"].met is True
    assert "I now use" in rows["non_self_sabotage"].evidence_quote
    assert rows["non_self_sabotage"].evidence_quote in answer
    assert result.required_missing == []
    assert result.errors == []
    assert result.blockers == []
    assert result.pass_eligible is True
    assert "frame the weakness honestly" not in result.next_focus.lower()
    assert "pressure-test" in result.next_focus.lower()


def test_interview_weakness_disqualifying_rejection_is_not_overridden():
    answer = (
        "A weakness I am managing is missing migration edge cases when I am moving fast. "
        "I now use a pre-deploy checklist covering lock risk, regional timing, rollback commands, "
        "alert ownership, and reviewer sign-off. Since adopting it, two schema changes shipped "
        "without checkout errors, and rollback readiness improved from ad hoc notes to a tested "
        "command runbook."
    )
    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    reason = (
        "Although it is not disqualifying in every role, it violates a core role "
        "requirement for this position."
    )
    model_eval = PrepRubricEval(
        raw_score=0.79,
        criteria=[
            CriterionEval(id="real_weakness", met=True, evidence_quote="missing migration edge cases"),
            CriterionEval(id="mitigation_habit", met=True, evidence_quote="pre-deploy checklist"),
            CriterionEval(id="progress_evidence", met=False, reason="no completed result"),
            CriterionEval(id="non_self_sabotage", met=False, reason=reason),
        ],
        required_missing=["progress_evidence", "non_self_sabotage"],
        errors=["missing required rubric proof: progress_evidence, non_self_sabotage"],
        next_focus="Choose a weakness that does not violate a core role requirement.",
        pass_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["progress_evidence"].met is True
    assert rows["non_self_sabotage"].met is False
    assert rows["non_self_sabotage"].reason == reason
    assert result.required_missing == ["non_self_sabotage"]
    assert result.errors == ["missing required rubric proof: non_self_sabotage"]
    assert result.blockers == ["missing_required:non_self_sabotage"]
    assert result.pass_eligible is False
    assert result.next_focus == "Choose a weakness that does not violate a core role requirement."


def test_interview_weakness_contradictory_role_failure_admission_stays_rejected():
    answer = (
        "A weakness I am managing is that I avoid incident ownership and refuse to "
        "escalate production risk. I now use a 15-minute escalation rule. Across the last "
        "three payment incidents, escalation time fell from 40 minutes to 12. This does "
        "not prevent me from working on incidents, and I still own diagnosis."
    )
    state = svc._new_state(
        "user-1", "session-role-failure", "int_03_weakness_framing", [],
        task_type="interview_prep",
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    reason = "The weakness violates a core role requirement for incident ownership and escalation."
    model_eval = PrepRubricEval(
        raw_score=0.79,
        criteria=[
            CriterionEval(id="real_weakness", met=True, evidence_quote="avoid incident ownership"),
            CriterionEval(id="mitigation_habit", met=True, evidence_quote="15-minute escalation rule"),
            CriterionEval(id="progress_evidence", met=True, evidence_quote="fell from 40 minutes to 12"),
            CriterionEval(id="non_self_sabotage", met=False, reason=reason),
        ],
        required_missing=["non_self_sabotage"],
        next_focus="Choose a weakness that does not violate a core role requirement.",
        pass_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["non_self_sabotage"].met is False
    assert result.pass_eligible is False
    assert result.required_missing == ["non_self_sabotage"]


def test_interview_weakness_transfer_context_repairs_false_model_rejection():
    core_answer = (
        "A weakness I am managing is missing migration edge cases when I am moving fast. "
        "I now use a deployment checklist. Since adopting it, two schema changes shipped "
        "without checkout errors."
    )
    answer = (
        "A weakness I am managing is committing to estimates before hidden dependencies are clear. "
        "I now separate a discovery estimate from a delivery estimate, list assumptions, and "
        "re-estimate after a short technical spike. Since adopting that habit, estimate variance "
        "across my last three backend changes fell from roughly 40% to under 15%."
    )
    parent_id = "session-1:core"
    core_contract = {
        "context_id": "int_03_weakness_framing:independent:core",
        "semantic_anchors": [],
    }
    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    state.update({
        "active_prompt_attempt_type": "transfer",
        "active_task_contract": {
            "prompt_id": "transfer-prompt",
            "context_id": "int_03_weakness_framing:transfer:estimation",
            "semantic_anchors": [
                "estimation under ambiguity",
                "real weakness corrective habit when requirements uncertain measurable progress signal",
            ],
        },
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_03_weakness_framing",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": core_answer,
            "task_contract": core_contract,
        },
    })
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.85,
        criteria=[
            CriterionEval(id="real_weakness", met=True, evidence_quote=answer.split(".")[0] + "."),
            CriterionEval(id="mitigation_habit", met=True, evidence_quote="I now separate a discovery estimate from a delivery estimate, list assumptions, and re-estimate after a short technical spike."),
            CriterionEval(id="progress_evidence", met=True, evidence_quote="Since adopting that habit, estimate variance across my last three backend changes fell from roughly 40% to under 15%."),
            CriterionEval(id="non_self_sabotage", met=True, evidence_quote=answer.split(".")[0] + "."),
            CriterionEval(id="transfer_context", met=False, reason="new context not recognized"),
        ],
        required_missing=["transfer_context"],
        errors=["missing required rubric proof: transfer_context"],
        next_focus="Use the newly assigned scenario.",
        pass_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert packet.core_qualified is True
    assert rows["transfer_context"].met is True
    assert rows["transfer_context"].evidence_quote == answer.split(".")[0] + "."
    assert result.required_missing == []
    assert result.blockers == []
    assert result.pass_eligible is True

    from app.services import rubric_engine as engine

    partial_answer = (
        "A weakness I am managing is estimates under pressure. I now use a checklist habit, and my "
        "progress is measurable across recent delivery dates."
    )
    partial_packet = build_evaluation_packet(
        state,
        svc.get_node("int_03_weakness_framing"),
        partial_answer,
    )
    assert engine._has_assigned_interview_transfer_context(partial_packet) is False


def test_interview_weakness_reconciliation_rewrites_old_delivery_focus_when_core_already_met():
    answer = (
        "Earlier, I tended to explain technical implementation before business impact. "
        "I now start with the decision criteria, explain the tradeoff in plain language, "
        "and prove the outcome. In a payment rollout, that meant catching two retry edge "
        "cases early, avoiding a full rollback, and giving product a clear revenue-protection "
        "reason to expand gradually."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.8,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.76, evidence_quote="technical implementation"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.76, evidence_quote="decision criteria"),
            CriterionEval(id="progress_evidence", met=True, quality=0.76, evidence_quote="two retry edge cases"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.8, evidence_quote="I now start"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Practise delivering the three-part weakness answer concisely.",
        pass_eligible=True,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert result.pass_eligible is True
    assert "three-part weakness answer" not in result.next_focus.lower()
    assert "practise delivering" not in result.next_focus.lower()
    assert "pressure-test" in result.next_focus.lower()


def test_interview_weakness_shape_reconciliation_does_not_credit_generic_claims():
    answer = (
        "My weakness is jumping straight into technical details before business impact. "
        "I manage it with decision criteria first and a habit of comparing options. "
        "The result should be better outcomes, but I have not named a real case yet."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.7,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.65, evidence_quote="jumping straight"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.65, evidence_quote="decision criteria"),
            CriterionEval(id="progress_evidence", met=False, quality=0.1, reason="no real case"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.7, evidence_quote="I manage it"),
        ],
        required_missing=["progress_evidence"],
        errors=["missing required rubric proof: progress_evidence"],
        next_focus="Add a real progress example.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert result.pass_eligible is False
    assert result.effective_score < packet.pass_score


def test_interview_weakness_shape_reconciliation_rejects_loose_meeting_claim():
    answer = (
        "I used to over-explain technical trade-offs. Now I use decision criteria first, "
        "and it helped in a meeting."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.72,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.65, evidence_quote="over-explain"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.65, evidence_quote="decision criteria"),
            CriterionEval(id="progress_evidence", met=False, quality=0.2, reason="too generic"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.7, evidence_quote="Now I use"),
        ],
        required_missing=["progress_evidence"],
        errors=["missing required rubric proof: progress_evidence"],
        next_focus="Add a real progress example.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert result.pass_eligible is False
    assert result.effective_score < packet.pass_score


def test_interview_weakness_overcredit_is_capped_without_concrete_progress():
    answer = (
        "I used to over-explain technical trade-offs. Now I use decision criteria first, "
        "and it helped in a meeting."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="over-explain technical trade-offs"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="helped in a meeting"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="Now I use"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert "minimum_gate:progress_evidence" in result.blockers
    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert result.effective_score < packet.pass_score


def test_interview_pitch_overcredit_is_capped_without_specific_proof():
    answer = "I'm a backend engineer. I improved things. Now I want to own larger systems."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.88,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="improved things"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own larger systems"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert result.effective_score < packet.pass_score


def test_interview_pitch_detail_gate_does_not_match_api_inside_word():
    answer = "I'm a backend engineer. I improved capital planning. Now I want to lead platform work."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.88,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="capital planning"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="lead platform work"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False


def test_interview_pitch_gate_requires_direction_for_pitch_structure():
    answer = "I'm a backend engineer. I built FastAPI payment APIs."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote=""),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "pitch_structure" in result.required_missing
    assert "minimum_gate:pitch_structure" in result.blockers
    assert result.pass_eligible is False
    assert result.mastery_eligible is False


def test_interview_pitch_worked_on_domain_noun_is_not_specific_detail():
    answer = "I'm a backend engineer. I worked on payment services. I want to lead platform reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="worked on payment services"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="lead platform reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False
    assert result.mastery_eligible is False


@pytest.mark.parametrize(
    ("answer", "role_quote", "future_quote"),
    [
        pytest.param(
            "I'm a sales manager. I managed customers. I want to grow into leadership.",
            "sales manager",
            "grow into leadership",
            id="managed-customers",
        ),
        pytest.param(
            "I'm a marketing manager. I improved campaigns. I want to lead growth.",
            "marketing manager",
            "lead growth",
            id="improved-campaigns",
        ),
        pytest.param(
            "I'm a product manager. I built things for customers. I want to own larger products.",
            "product manager",
            "own larger products",
            id="built-things-for-customers",
        ),
    ],
)
def test_interview_pitch_generic_action_domain_claim_cannot_override_model_failure(
    answer,
    role_quote,
    future_quote,
):
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": role_quote.title()},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.3,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.5, evidence_quote=role_quote),
            CriterionEval(id="specific_detail", met=False, quality=0.2, reason="generic domain claim"),
            CriterionEval(id="pitch_structure", met=False, quality=0.2, reason="no concrete proof"),
            CriterionEval(id="future_goal", met=True, quality=0.5, evidence_quote=future_quote),
        ],
        required_missing=["specific_detail", "pitch_structure"],
        errors=["missing required rubric proof: specific_detail, pitch_structure"],
        next_focus="Add concrete proof.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)
    rows = {row.id: row for row in result.criteria}

    assert rows["specific_detail"].met is False
    assert rows["pitch_structure"].met is False
    assert "specific_detail" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert result.effective_score == 0.3
    assert result.effective_score < packet.pass_score
    assert result.pass_eligible is False
    assert result.mastery_eligible is False


def test_interview_pitch_domain_noun_without_proof_is_not_specific_detail():
    answer = "I'm a backend engineer. I want to own payment systems."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="payment systems"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own payment systems"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False


def test_interview_pitch_gate_accepts_non_software_specific_proof():
    answer = (
        "I'm a sales manager focused on enterprise renewals. "
        "I led a renewal process that reduced churn by 12%. "
        "I want to grow into revenue leadership."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Sales Manager"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="sales manager"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="reduced churn by 12%"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="sales manager"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="revenue leadership"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert result.pass_eligible is True


def test_interview_pitch_identity_gate_rejects_project_without_role_identity():
    answer = "In a project, I built FastAPI payment APIs, and I want to own platform reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="project"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="project"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own platform reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "answers_question" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert "minimum_gate:answers_question" in result.blockers
    assert result.pass_eligible is False


def test_interview_pitch_identity_gate_accepts_nurse_with_specific_proof():
    answer = (
        "I'm a nurse focused on safer ward handoffs. "
        "I reduced medication errors by 20% with a checklist. "
        "I want to grow into ward leadership."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Nurse"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="nurse"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="medication errors by 20%"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="nurse focused on safer ward handoffs"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="ward leadership"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert result.pass_eligible is True


def test_interview_pitch_identity_gate_rejects_future_leader_without_current_role():
    answer = "I built FastAPI payment APIs, and I want to grow as a leader."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="leader"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="grow as a leader"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="grow as a leader"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "answers_question" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_identity_gate_rejects_future_known_role_without_current_identity():
    answer = "I built FastAPI payment APIs, and I want to grow as a backend engineer."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="grow as a backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="grow as a backend engineer"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "answers_question" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_identity_gate_rejects_future_role_before_marker():
    answer = "Backend engineer is my next role. I built FastAPI payment APIs."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="Backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="Backend engineer is my next role"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="next role"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "answers_question" in result.required_missing
    assert "pitch_structure" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_identity_gate_accepts_lead_backend_engineering_phrasing():
    answer = (
        "I lead backend engineering for payment reliability. "
        "I reduced checkout incidents by 30%. "
        "I want to own platform reliability."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineering"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="reduced checkout incidents by 30%"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="lead backend engineering"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own platform reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert result.pass_eligible is True


def test_interview_pitch_negated_proof_is_capped():
    answer = "I'm a backend engineer. I haven't built FastAPI payment APIs yet, but I want to own reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="haven't built FastAPI payment APIs yet"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert "minimum_gate:specific_detail" in result.blockers
    assert result.pass_eligible is False


def test_interview_pitch_did_not_work_on_negated_proof_is_capped():
    answer = "I'm a backend engineer. I did not work on payment APIs, but I want to own reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="did not work on payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_do_not_work_on_negated_proof_is_capped():
    answer = "I'm a backend engineer. I don't work on payment APIs yet, but I want to own reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="don't work on payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert result.pass_eligible is False


def test_interview_pitch_no_project_where_built_negated_proof_is_capped():
    answer = "I'm a backend engineer. I don't have a project where I built payment APIs yet, but I want to own reliability."
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_01_elevator_pitch"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="answers_question", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="project where I built payment APIs"),
            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer"),
            CriterionEval(id="future_goal", met=True, quality=0.9, evidence_quote="own reliability"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "specific_detail" in result.required_missing
    assert result.pass_eligible is False


def test_interview_weakness_generic_customer_progress_is_capped():
    answer = (
        "I used to over-explain technical trade-offs. "
        "Now I use decision criteria first. "
        "This helped a customer and improved stakeholder confidence."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="over-explain technical trade-offs"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="helped a customer"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="Now I use"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert "minimum_gate:progress_evidence" in result.blockers
    assert result.pass_eligible is False


def test_interview_weakness_customer_meeting_vague_progress_is_capped():
    answer = (
        "I used to over-explain technical trade-offs. "
        "Now I use decision criteria first. "
        "In a customer meeting, this helped the customer and improved stakeholder confidence."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="over-explain technical trade-offs"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="improved stakeholder confidence"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="Now I use"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert "minimum_gate:progress_evidence" in result.blockers
    assert result.pass_eligible is False


def test_interview_weakness_no_concrete_example_negation_is_capped():
    answer = (
        "I used to over-explain technical trade-offs. "
        "Now I use decision criteria first. "
        "I don't have a concrete example yet, but in a customer meeting this helped the customer."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="over-explain technical trade-offs"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="customer meeting"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="Now I use"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert result.pass_eligible is False


def test_interview_weakness_real_gate_rejects_sometimes_without_weakness():
    answer = (
        "Sometimes I help customers. "
        "I now use decision criteria first. "
        "In a customer escalation, that resolved the issue."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="Sometimes"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="resolved the issue"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="I now"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "real_weakness" in result.required_missing
    assert "minimum_gate:real_weakness" in result.blockers
    assert result.pass_eligible is False


def test_interview_weakness_real_gate_rejects_used_to_without_weak_behavior():
    answer = (
        "I used to help customers. "
        "I now use decision criteria first. "
        "In a customer escalation, that resolved the issue."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="used to"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="resolved the issue"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="I now"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert "real_weakness" in result.required_missing
    assert result.pass_eligible is False


def test_interview_weakness_real_gate_accepts_jump_to_implementation_phrasing():
    answer = (
        "I tend to jump straight into implementation before explaining business impact. "
        "I now lead with decision criteria first. "
        "In a payment rollout, that helped the team catch two retry edge cases and avoid a rollback."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="real_weakness", met=True, quality=0.9, evidence_quote="jump straight into implementation"),
            CriterionEval(id="mitigation_habit", met=True, quality=0.9, evidence_quote="decision criteria first"),
            CriterionEval(id="progress_evidence", met=True, quality=0.9, evidence_quote="catch two retry edge cases"),
            CriterionEval(id="non_self_sabotage", met=True, quality=0.9, evidence_quote="I now"),
        ],
        required_missing=[],
        errors=[],
        next_focus="Try a pressure version.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert result.pass_eligible is True


def test_interview_weakness_complete_answer_repairs_inconsistent_model_proof():
    answer = (
        "Earlier, I led with technical implementation before business impact. "
        "I changed that by opening with decision criteria and explaining the tradeoff "
        "in plain language. In a phased payment migration, we caught two retry defects "
        "before full rollout, kept checkout failure rate below 0.3%, and avoided a rollback."
    )
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Engineer"},
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.79,
        criteria=[
            CriterionEval(
                id="real_weakness",
                met=True,
                quality=0.79,
                evidence_quote="led with implementation instead of impact",
            ),
            CriterionEval(
                id="mitigation_habit",
                met=True,
                quality=0.79,
                evidence_quote="opened with business criteria",
            ),
            CriterionEval(
                id="progress_evidence",
                met=True,
                quality=0.79,
                evidence_quote="reduced checkout failures and prevented rollback",
            ),
            CriterionEval(
                id="non_self_sabotage",
                met=True,
                quality=0.8,
                evidence_quote="I changed that",
            ),
        ],
        required_missing=["progress_evidence"],
        errors=["missing required rubric proof: progress_evidence"],
        next_focus="Refine the transition between mitigation and evidence of progress.",
        pass_eligible=False,
        mastery_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert result.required_missing == []
    assert not any(blocker.startswith("invalid_proof:") for blocker in result.blockers)
    assert result.pass_eligible is True
    assert "pressure-test" in result.next_focus.lower()


def test_interview_weakness_hypothetical_progress_is_not_reconciled_to_pass():
    answer = (
        "Earlier, I led with technical implementation before business impact. "
        "I changed that by opening with decision criteria. In a payment rollout, "
        "I would have prevented a rollback and reduced support tickets by 20%."
    )
    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.3,
        criteria=[
            CriterionEval(id="real_weakness", met=True, evidence_quote="technical implementation before business impact"),
            CriterionEval(id="mitigation_habit", met=True, evidence_quote="opening with decision criteria"),
            CriterionEval(id="progress_evidence", met=False, reason="hypothetical outcome"),
            CriterionEval(id="non_self_sabotage", met=True, evidence_quote="I changed that"),
        ],
        required_missing=["progress_evidence"],
        next_focus="Give an actual completed result.",
        pass_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert result.pass_eligible is False


def test_interview_weakness_third_party_progress_is_not_reconciled_to_pass():
    answer = (
        "Earlier, I led with technical implementation before business impact. "
        "I changed that by opening with decision criteria. In a payment rollout, "
        "the team prevented a rollback and reduced support tickets by 20%."
    )
    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.3,
        criteria=[
            CriterionEval(id="real_weakness", met=True, evidence_quote="technical implementation before business impact"),
            CriterionEval(id="mitigation_habit", met=True, evidence_quote="opening with decision criteria"),
            CriterionEval(id="progress_evidence", met=False, reason="no learner-owned result"),
            CriterionEval(id="non_self_sabotage", met=True, evidence_quote="I changed that"),
        ],
        required_missing=["progress_evidence"],
        next_focus="Name what you personally changed and achieved.",
        pass_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    assert "progress_evidence" in result.required_missing
    assert result.pass_eligible is False


def test_interview_weakness_indirect_hypothetical_and_observer_results_are_capped():
    variants = (
        "I would say we prevented a rollback and reduced support tickets by 20%.",
        "I watched while the team prevented a rollback and reduced support tickets by 20%.",
        "I heard that our rollout prevented a rollback and reduced support tickets by 20%.",
        "I was told our fix prevented a rollback and reduced support tickets by 20%.",
        "I observed that the rollout prevented a rollback and reduced support tickets by 20%.",
        "I was informed that our rollout prevented a rollback and reduced support tickets by 20%.",
        "My manager told me our fix prevented a rollback and reduced support tickets by 20%.",
        "According to my manager, our rollout prevented a rollback and reduced support tickets by 20%.",
    )
    for result_sentence in variants:
        answer = (
            "Earlier, I led with technical implementation before business impact. "
            "I changed that by opening with decision criteria. In a payment rollout, "
            f"{result_sentence}"
        )
        state = svc._new_state(
            "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
        )
        packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
        model_eval = PrepRubricEval(
            raw_score=0.3,
            criteria=[
                CriterionEval(id="real_weakness", met=True, evidence_quote="technical implementation before business impact"),
                CriterionEval(id="mitigation_habit", met=True, evidence_quote="opening with decision criteria"),
                CriterionEval(id="progress_evidence", met=False, reason="not an owned completed outcome"),
                CriterionEval(id="non_self_sabotage", met=True, evidence_quote="I changed that"),
            ],
            required_missing=["progress_evidence"],
            next_focus="Give an owned completed result.",
            pass_eligible=False,
        )

        result = apply_caps(packet, model_eval)

        assert "progress_evidence" in result.required_missing
        assert result.pass_eligible is False


def test_pressure_followup_uses_parent_grounded_stage_rubric():
    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    state.update({
        "active_prompt_attempt_type": "pressure",
        "core_qualified": True,
        "core_qualification_turn_id": "turn-core-2",
        "core_qualification_evidence": {
            "evaluation_id": "turn-core-2",
            "user_id": "user-1",
            "node_id": "int_03_weakness_framing",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": (
                "My weakness was rushing rollouts; I now use phased pilots and decision gates, "
                "which held duplicate charges at zero and reduced support tickets by 22%."
            ),
        },
    })
    answer = (
        "I would defend the phased rollout because the pilot held duplicate charges at "
        "zero and reduced support tickets by 22%, so the slower option protected revenue."
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.88,
        criteria=[
            CriterionEval(id="pressure_response", met=True, evidence_quote="defend the phased rollout"),
            CriterionEval(id="evidence_defense", met=True, evidence_quote="reduced support tickets by 22%"),
            CriterionEval(id="core_consistency", met=True, evidence_quote="slower option protected revenue"),
        ],
        required_missing=[],
        next_focus="Try a different interviewer objection.",
        pass_eligible=True,
        mastery_eligible=True,
    )

    result = apply_caps(packet, model_eval)

    assert packet.core_qualified is True
    assert packet.core_qualification_turn_id == "turn-core-2"
    assert [criterion["id"] for criterion in packet.criteria] == [
        "pressure_response", "evidence_defense", "core_consistency"
    ]
    assert result.required_missing == []
    assert result.pass_eligible is True
    assert result.attempt_type == "pressure"


def test_failure_pressure_direct_answer_repairs_mislabeled_pressure_response():
    state = svc._new_state(
        "user-1", "session-int06-live-pressure", "int_06_own_a_failure", [], task_type="interview_prep"
    )
    parent_id = "session-int06-live-pressure:turn-core:int_06_own_a_failure"
    state.update({
        "messages": [
            {
                "role": "assistant",
                "content": "Why should I trust your judgment after that failure?",
            }
        ],
        "active_prompt_attempt_type": "pressure",
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_06_own_a_failure",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": (
                "On a search-service rollout, I removed a database index before replaying "
                "production traffic. The API timed out for 8% of requests. I restored the "
                "index and added query replays and rollback rehearsals."
            ),
        },
    })
    answer = (
        "You should trust my judgment because I owned the database-index decision and the "
        "resulting 8% timeout rate. I restored the index, coordinated the customer-status "
        "update, then made production-like query replays and rollback rehearsals mandatory."
    )
    packet = build_evaluation_packet(state, svc.get_node("int_06_own_a_failure"), answer)
    model_eval = PrepRubricEval(
        raw_score=0.82,
        criteria=[
            CriterionEval(
                id="pressure_response",
                met=False,
                quality=0.4,
                reason="did not directly answer the pushback",
            ),
            CriterionEval(
                id="evidence_defense",
                met=True,
                quality=0.85,
                evidence_quote="You should trust my judgment because I owned the database-index decision and the resulting 8% timeout rate",
            ),
            CriterionEval(
                id="core_consistency",
                met=True,
                quality=0.85,
                evidence_quote="I restored the index",
            ),
        ],
        required_missing=["pressure_response"],
        next_focus="Answer the pushback directly.",
        pass_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    rows = {row.id: row for row in result.criteria}
    assert rows["pressure_response"].met is True
    assert rows["pressure_response"].evidence_quote.startswith("You should trust my judgment because")
    assert result.required_missing == []
    assert result.pass_eligible is True


def test_int07_live_clarifier_and_focused_answer_repair_model_false_negative():
    state = svc._new_state(
        "user-1",
        "session-int07-live-answer",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "Can you talk about a time when you faced a difficult technical challenge?",
    }]
    answer = (
        "Before I answer, would you like a challenge centered on system design or incident "
        "response, and should I emphasize technical diagnosis or decision-making under "
        "pressure? If incident response is the focus, I would discuss a payment retry "
        "incident where I traced partial-timeout duplicates, paused the rollout, introduced "
        "idempotency keys, and prevented repeat duplicate holds in the following quarter."
    )
    packet = build_evaluation_packet(
        state,
        svc.get_node("int_07_clarify_before_answering"),
        answer,
    )
    model_eval = PrepRubricEval(
        raw_score=0.2,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=False, reason="ambiguity not explicit"),
            CriterionEval(id="asks_targeted_question", met=False, reason="no clarifier"),
            CriterionEval(id="states_answer_frame", met=False, reason="no focused answer"),
            CriterionEval(id="professional_tone", met=True, evidence_quote="Before I answer"),
        ],
        required_missing=[
            "recognizes_ambiguity",
            "asks_targeted_question",
            "states_answer_frame",
        ],
        errors=[
            "missing required rubric proof: recognizes_ambiguity, asks_targeted_question, states_answer_frame"
        ],
        next_focus="Ask a clarifying question.",
        pass_eligible=False,
    )

    result = apply_caps(packet, model_eval)

    rows = {row.id: row for row in result.criteria}
    for criterion_id in (
        "recognizes_ambiguity",
        "asks_targeted_question",
        "states_answer_frame",
    ):
        assert rows[criterion_id].met is True
        assert rows[criterion_id].evidence_quote
    assert result.required_missing == []
    assert result.pass_eligible is True
    assert result.effective_score == 0.7
    assert result.errors == []
    assert "different ambiguous interview question" in result.next_focus
    credit = compute_attempt_credit({}, result)
    assert credit["readiness_score"] == 0.7
    assert credit["independent_passes"] == 1
    assert "ask a clarifying question" not in credit["last_gap"].lower()


def test_int07_failed_structural_repair_uses_only_backend_provable_evidence(monkeypatch):
    from app.ai import calls

    answer = (
        "Before I answer, would you like a challenge centered on system design or incident "
        "response? If incident response is the focus, I would discuss how I traced duplicate "
        "payment retries, paused the rollout, and introduced idempotency keys."
    )
    first = PrepRubricEval(
        raw_score=0.2,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=True, evidence_quote="invented ambiguity"),
            CriterionEval(id="asks_targeted_question", met=True, evidence_quote="invented question"),
            CriterionEval(id="states_answer_frame", met=True, evidence_quote="invented answer"),
            CriterionEval(id="professional_tone", met=True, evidence_quote="Before I answer"),
        ],
        required_missing=[],
        next_focus="Ask a clarification.",
        pass_eligible=True,
    )
    call_count = 0

    async def fake_structured(_prompt, _schema):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return first
        raise TimeoutError("repair model unavailable")

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)
    state = svc._new_state(
        "user-1",
        "session-int07-repair-fallback",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "Can you talk about a time when you faced a difficult technical challenge?",
    }]

    result = _run(calls.evaluate_prep_answer(
        svc.get_node("int_07_clarify_before_answering"),
        state["messages"],
        answer,
        state=state,
    ))

    assert call_count == 2
    assert result.pass_eligible is True
    assert result.required_missing == []
    assert result.effective_score == 0.7


def test_int07_invalid_repair_proof_uses_backend_provable_fallback(monkeypatch):
    from app.ai import calls

    answer = (
        "Before I answer, do you mean system design or incident response? If incident response, "
        "I would explain how I traced duplicate retries, paused the rollout, and added idempotency keys."
    )
    first = PrepRubricEval(
        raw_score=0.2,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=True, evidence_quote="invented ambiguity"),
            CriterionEval(id="asks_targeted_question", met=True, evidence_quote="invented question"),
            CriterionEval(id="states_answer_frame", met=True, evidence_quote="invented answer"),
            CriterionEval(id="professional_tone", met=True, evidence_quote="Before I answer"),
        ],
        required_missing=[],
        next_focus="Ask a clarification.",
        pass_eligible=True,
    )
    invalid_repair = PrepRubricEval(
        raw_score=0.9,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=True, evidence_quote="fabricated repair ambiguity"),
            CriterionEval(id="asks_targeted_question", met=True, evidence_quote="fabricated repair question"),
            CriterionEval(id="states_answer_frame", met=True, evidence_quote="fabricated repair answer"),
        ],
        required_missing=[],
        next_focus="Fabricated repair.",
        pass_eligible=True,
    )
    outputs = [first, invalid_repair]

    async def fake_structured(_prompt, _schema):
        return outputs.pop(0)

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)
    state = svc._new_state(
        "user-1",
        "session-int07-invalid-repair-proof",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "Can you talk about a time when you faced a difficult technical challenge?",
    }]

    result = _run(calls.evaluate_prep_answer(
        svc.get_node("int_07_clarify_before_answering"),
        state["messages"],
        answer,
        state=state,
    ))

    assert outputs == []
    assert result.pass_eligible is True
    assert result.required_missing == []
    assert all("fabricated" not in row.evidence_quote for row in result.criteria)


def test_prep_optional_fabricated_evidence_is_repaired_before_memory_can_use_it(monkeypatch):
    from app.ai import calls

    answer = (
        "Before I answer, do you mean system design or incident response? If incident response, "
        "I would explain how I traced duplicate retries, paused the rollout, and added idempotency keys."
    )
    first = PrepRubricEval(
        raw_score=0.8,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=True, evidence_quote="system design or incident response"),
            CriterionEval(id="asks_targeted_question", met=True, evidence_quote="do you mean system design or incident response?"),
            CriterionEval(id="states_answer_frame", met=True, evidence_quote="If incident response"),
            CriterionEval(id="professional_tone", met=True, evidence_quote="invented professional wording"),
        ],
        required_missing=[],
        next_focus="Apply it again.",
        pass_eligible=True,
    )
    repair = PrepRubricEval(
        raw_score=0.8,
        criteria=[
            CriterionEval(id="professional_tone", met=False, evidence_quote="", reason="no exact optional proof"),
        ],
        required_missing=[],
        next_focus="Apply it again.",
        pass_eligible=True,
    )
    outputs = [first, repair]

    async def fake_structured(_prompt, _schema):
        return outputs.pop(0)

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)
    state = svc._new_state(
        "user-1",
        "session-int07-optional-proof",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "Can you talk about a time when you faced a difficult technical challenge?",
    }]

    result = _run(calls.evaluate_prep_answer(
        svc.get_node("int_07_clarify_before_answering"),
        state["messages"],
        answer,
        state=state,
    ))

    optional = next(row for row in result.criteria if row.id == "professional_tone")
    assert outputs == []
    assert optional.met is False
    assert optional.evidence_quote == ""
    assert result.pass_eligible is True


def test_int07_internal_repair_merge_error_is_not_silently_scored(monkeypatch):
    from app.ai import calls

    first = PrepRubricEval(
        raw_score=0.2,
        criteria=[],
        required_missing=[],
        next_focus="Missing rows.",
        pass_eligible=False,
    )
    repair = PrepRubricEval(
        raw_score=0.2,
        criteria=[],
        required_missing=[],
        next_focus="Still missing rows.",
        pass_eligible=False,
    )
    outputs = [first, repair]

    async def fake_structured(_prompt, _schema):
        return outputs.pop(0)

    def broken_merge(*_args, **_kwargs):
        raise AssertionError("internal merge defect")

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)
    monkeypatch.setattr(calls, "_merge_structural_repair", broken_merge)
    state = svc._new_state(
        "user-1",
        "session-int07-internal-merge-error",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )

    with pytest.raises(AssertionError, match="internal merge defect"):
        _run(calls.evaluate_prep_answer(
            svc.get_node("int_07_clarify_before_answering"),
            [],
            "Before I answer, do you mean system design or incident response?",
            state=state,
        ))


def test_int07_accepts_natural_multi_option_clarifier_with_focused_answer():
    state = svc._new_state(
        "user-1",
        "session-int07-natural-clarifier",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    answer = (
        "Could you clarify whether you mean reliability, latency, or cost? I'll focus on reliability: "
        "I would start with the highest-severity failure modes, add service-level alerts, and "
        "verify the rollback path before changing traffic."
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "How would you improve the technical performance of this service?",
    }]
    packet = build_evaluation_packet(state, svc.get_node("int_07_clarify_before_answering"), answer)
    raw = PrepRubricEval(
        raw_score=0.3,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=False),
            CriterionEval(id="asks_targeted_question", met=False),
            CriterionEval(id="states_answer_frame", met=False),
            CriterionEval(id="professional_tone", met=True, evidence_quote="Which aspect matters most"),
        ],
        required_missing=["recognizes_ambiguity", "asks_targeted_question", "states_answer_frame"],
        next_focus="Ask a clarifying question.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is True
    assert result.required_missing == []


@pytest.mark.parametrize(
    "answer",
    [
        "Could you clarify the question? I would describe a payment incident and its result.",
        "Do you mean system design or incident response?",
        "I would focus on incident response and explain how I stopped duplicate retries.",
    ],
)
def test_int07_does_not_invent_complete_clarification_evidence(answer):
    state = svc._new_state(
        "user-1",
        "session-int07-incomplete-shape",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "Can you talk about a time when you faced a difficult technical challenge?",
    }]
    packet = build_evaluation_packet(state, svc.get_node("int_07_clarify_before_answering"), answer)
    raw = PrepRubricEval(
        raw_score=0.3,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=False),
            CriterionEval(id="asks_targeted_question", met=False),
            CriterionEval(id="states_answer_frame", met=False),
            CriterionEval(id="professional_tone", met=True, evidence_quote=answer[:40]),
        ],
        required_missing=["recognizes_ambiguity", "asks_targeted_question", "states_answer_frame"],
        next_focus="Ask a clarifying question.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    assert result.required_missing


def test_int07_does_not_credit_unrelated_a_or_b_question():
    state = svc._new_state(
        "user-1",
        "session-int07-unrelated-clarifier",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "Can you talk about a time when you faced a difficult technical challenge?",
    }]
    answer = (
        "Could you clarify whether you prefer coffee or tea? If coffee, I would choose a dark "
        "roast because it has a stronger flavor and works better in the morning."
    )
    packet = build_evaluation_packet(state, svc.get_node("int_07_clarify_before_answering"), answer)
    raw = PrepRubricEval(
        raw_score=0.3,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=False),
            CriterionEval(id="asks_targeted_question", met=False),
            CriterionEval(id="states_answer_frame", met=False),
            CriterionEval(id="professional_tone", met=True, evidence_quote="Could you clarify"),
        ],
        required_missing=["recognizes_ambiguity", "asks_targeted_question", "states_answer_frame"],
        next_focus="Ask a relevant clarifying question.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    assert "asks_targeted_question" in result.required_missing


@pytest.mark.parametrize(
    "answer",
    [
        (
            "Before I answer, do you mean system design or incident response? "
            "If incident response, I made a decision to bake bread on weekends and prefer "
            "sourdough because it tastes better."
        ),
        (
            "Before I answer, do you mean system design or incident response? "
            "If incident response, I improved service at my bakery by greeting customers "
            "warmly every morning."
        ),
    ],
)
def test_int07_does_not_credit_relevant_clarifier_with_unrelated_answer_body(answer):
    state = svc._new_state(
        "user-1",
        "session-int07-unrelated-answer-body",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "Can you talk about a time when you faced a difficult technical challenge?",
    }]
    packet = build_evaluation_packet(state, svc.get_node("int_07_clarify_before_answering"), answer)
    raw = PrepRubricEval(
        raw_score=0.2,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=False),
            CriterionEval(id="asks_targeted_question", met=False),
            CriterionEval(id="states_answer_frame", met=False),
            CriterionEval(id="professional_tone", met=True, evidence_quote="Before I answer"),
        ],
        required_missing=["recognizes_ambiguity", "asks_targeted_question", "states_answer_frame"],
        next_focus="Answer the selected scope.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    assert "states_answer_frame" in result.required_missing


@pytest.mark.parametrize(
    ("prompt", "answer", "expected_pass"),
    [
        (
            "Tell me about the checkout outage on March 3. Focus specifically on incident "
            "response and the rollback decision.",
            (
                "Do you mean system design or incident response? If incident response, I traced "
                "retry failures, paused the rollout, and verified the rollback before restoring traffic."
            ),
            False,
        ),
        (
            "Can you talk about a time when you faced a difficult technical challenge?",
            (
                "Do you mean system design or incident response? If incident response, I monitor "
                "my marathon performance, track alerts on my fitness watch, and adjust my weekend training plan."
            ),
            False,
        ),
        (
            "Can you talk about a time when you faced a difficult technical challenge?",
            (
                "Do you mean system design or incident response? If system design, I would compare "
                "the available options against the constraints with the team, document why one "
                "option fits, and revisit it after launch."
            ),
            True,
        ),
        (
            (
                "A detailed response on incident response is useful, but focus on the vague prompt "
                "\"Should remote work be the default?\" What aspects of remote work should be explored?"
            ),
            (
                "Before I answer, do you mean whether remote work should be the default for team "
                "productivity or for widening hiring access? If hiring access is the focus, I would "
                "support remote-first work because it lets teams recruit across regions, while using "
                "documented onboarding and planned in-person collaboration."
            ),
            True,
        ),
    ],
)
def test_int07_deterministic_credit_requires_ambiguous_prompt_and_grounded_answer(
    prompt,
    answer,
    expected_pass,
):
    state = svc._new_state(
        "user-1",
        "session-int07-grounding-matrix",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{"role": "assistant", "content": prompt}]
    packet = build_evaluation_packet(state, svc.get_node("int_07_clarify_before_answering"), answer)
    raw = PrepRubricEval(
        raw_score=0.0,
        criteria=[],
        required_missing=["recognizes_ambiguity", "asks_targeted_question", "states_answer_frame"],
        next_focus="Use the clarification structure.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is expected_pass
    if expected_pass:
        rows = {row.id: row for row in result.criteria}
        assert rows["states_answer_frame"].met is True


def test_int07_successful_structural_repair_clears_stale_target_missing(monkeypatch):
    from app.ai import calls

    answer = (
        "Before I answer, do you mean system design or incident response? If incident response, "
        "I would explain how I traced duplicate retries, paused the rollout, and added idempotency keys."
    )
    first = PrepRubricEval(
        raw_score=0.78,
        criteria=[
            CriterionEval(id="recognizes_ambiguity", met=True, evidence_quote="system design or incident response"),
            CriterionEval(id="states_answer_frame", met=True, evidence_quote="If incident response"),
            CriterionEval(id="professional_tone", met=True, evidence_quote="Before I answer"),
        ],
        required_missing=["asks_targeted_question"],
        next_focus="Ask a targeted question.",
        pass_eligible=False,
    )
    repair = PrepRubricEval(
        raw_score=0.78,
        criteria=[
            CriterionEval(
                id="asks_targeted_question",
                met=True,
                quality=0.85,
                evidence_quote="do you mean system design or incident response?",
            ),
        ],
        required_missing=[],
        next_focus="Use the clarified scope.",
        pass_eligible=True,
    )
    outputs = [first, repair]

    async def fake_structured(_prompt, _schema):
        return outputs.pop(0)

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", fake_structured)
    state = svc._new_state(
        "user-1",
        "session-int07-stale-missing",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "Can you talk about a time when you faced a difficult technical challenge?",
    }]

    result = _run(calls.evaluate_prep_answer(
        svc.get_node("int_07_clarify_before_answering"),
        state["messages"],
        answer,
        state=state,
    ))

    assert outputs == []
    assert result.required_missing == []
    assert result.pass_eligible is True


def test_int07_clean_feedback_stays_in_interview_and_sets_fresh_clarification_task():
    answer = (
        "Before I answer, do you mean system design or incident response? If incident "
        "response, I would explain how I stopped duplicate payment retries."
    )
    state = svc._new_state(
        "user-1",
        "session-int07-clean-feedback",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": answer,
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "independent",
            "criteria": [
                {"id": "recognizes_ambiguity", "met": True, "evidence_quote": "system design or incident response"},
                {"id": "asks_targeted_question", "met": True, "evidence_quote": "do you mean system design or incident response?"},
                {"id": "states_answer_frame", "met": True, "evidence_quote": "If incident response"},
            ],
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_fresh_independent",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "Let's discuss whether remote work should be the default. Ask about remote work.",
        state,
        "teach",
    )

    assert "remote work" not in cleaned.lower()
    assert "leadership" in cleaned.lower()
    assert "people management" in cleaned.lower()
    assert "technical direction" in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_int07_partial_feedback_names_only_missing_answer_frame():
    answer = "Before I answer, do you mean system design or incident response?"
    state = svc._new_state(
        "user-1",
        "session-int07-partial-feedback",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": answer,
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["states_answer_frame"],
            "blockers": ["missing_required:states_answer_frame"],
            "attempt_type": "independent",
            "criteria": [
                {"id": "recognizes_ambiguity", "met": True, "evidence_quote": "system design or incident response"},
                {"id": "asks_targeted_question", "met": True, "evidence_quote": answer},
                {"id": "states_answer_frame", "met": False, "evidence_quote": ""},
            ],
        },
        "tutor_turn_plan": {
            "verdict": "partial",
            "next_action": "rewrite",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "Everything is missing. Switch to remote work.",
        state,
        "teach",
    )

    assert "your clarifying question already narrows the scope" in cleaned.lower()
    assert "add a focused answer" in cleaned.lower()
    assert "remote work" not in cleaned.lower()
    assert "ask a clarifying question" not in cleaned.lower()


def test_int07_partial_feedback_does_not_relabel_nontechnical_prompt():
    state = svc._new_state(
        "user-1",
        "session-int07-leadership-partial",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": "Before I answer, do you mean people management or technical direction?",
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["asks_targeted_question", "states_answer_frame"],
            "blockers": [
                "missing_required:asks_targeted_question",
                "missing_required:states_answer_frame",
            ],
            "attempt_type": "independent",
            "criteria": [],
        },
        "tutor_turn_plan": {
            "verdict": "partial",
            "next_action": "rewrite",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response("Use the technical challenge again.", state, "teach")

    assert "same question" in cleaned.lower()
    assert "technical-challenge" not in cleaned.lower()


def test_int07_pressure_feedback_repairs_only_missing_core_consistency():
    state = svc._new_state(
        "user-1",
        "session-int07-pressure-partial",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": (
            "I will assume you mean technical direction. I would explain how I set the "
            "architecture boundary and review the decision with the team."
        ),
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["core_consistency"],
            "blockers": ["missing_required:core_consistency"],
            "attempt_type": "pressure",
            "criteria": [
                {
                    "id": "pressure_response",
                    "met": True,
                    "evidence_quote": "I will assume you mean technical direction",
                },
                {
                    "id": "evidence_defense",
                    "met": True,
                    "evidence_quote": "I set the architecture boundary and review the decision with the team",
                },
                {"id": "core_consistency", "met": False, "evidence_quote": ""},
            ],
        },
        "tutor_turn_plan": {
            "verdict": "partial",
            "next_action": "rewrite",
            "allowed_praise": False,
        },
        "core_qualified": True,
        "core_qualification_turn_id": "session-int07-pressure-partial:core",
        "core_qualification_evidence": {
            "evaluation_id": "session-int07-pressure-partial:core",
            "user_id": "user-1",
            "node_id": "int_07_clarify_before_answering",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": (
                "Before I answer, do you mean people management or technical direction? "
                "If technical direction, I would explain how I set architecture boundaries."
            ),
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "Ask another A-or-B clarification question.",
        state,
        "challenge",
    )

    assert "already answered the no-clarification pushback" in cleaned.lower()
    assert "connect that assumption to your earlier clarification" in cleaned.lower()
    assert "ask one concise a-or-b" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "pressure"


def test_int07_pressure_explicit_assumption_repairs_only_pressure_response():
    state = svc._new_state(
        "user-1",
        "session-int07-pressure-response-repair",
        "int_07_clarify_before_answering",
        [],
        task_type="interview_prep",
    )
    parent_id = "session-int07-pressure-response-repair:core"
    state.update({
        "active_prompt_attempt_type": "pressure",
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_07_clarify_before_answering",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": (
                "Before I answer, do you mean onboarding or reliability? If reliability, "
                "I would rank failure modes using incident data."
            ),
        },
    })
    answer = (
        "I will assume reliability is the priority, consistent with the product scope I just "
        "clarified. Under that assumption, I would use failed user journeys and incident "
        "frequency to rank failure modes, add service-level alerts, and track completion rate."
    )
    packet = build_evaluation_packet(state, svc.get_node("int_07_clarify_before_answering"), answer)
    raw = PrepRubricEval(
        raw_score=0.82,
        criteria=[
            CriterionEval(id="pressure_response", met=False, reason="assumption not explicit"),
            CriterionEval(
                id="evidence_defense",
                met=True,
                evidence_quote="use failed user journeys and incident frequency to rank failure modes",
            ),
            CriterionEval(
                id="core_consistency",
                met=True,
                evidence_quote="reliability is the priority, consistent with the product scope I just clarified",
            ),
        ],
        required_missing=["pressure_response"],
        next_focus="State the assumption.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    rows = {row.id: row for row in result.criteria}
    assert rows["pressure_response"].met is True
    assert rows["pressure_response"].evidence_quote == "I will assume reliability is the priority"
    assert result.required_missing == []
    assert result.pass_eligible is True


def test_int08_failed_structural_repair_uses_prompt_grounded_quantified_evidence(monkeypatch):
    from app.ai import calls

    answer = (
        "In the payment retry flow, duplicate holds affected 3.2% of timed-out transactions and "
        "status updates took about 18 seconds. I introduced idempotency keys, staged retries, and "
        "clearer observability; over six weeks duplicate holds fell to 0.2%, status latency dropped "
        "to 4 seconds, and related support tickets decreased by 42%."
    )
    first = PrepRubricEval(
        raw_score=0.1,
        criteria=[
            CriterionEval(id="impact_claim", met=True, evidence_quote="invented impact"),
            CriterionEval(id="quantified_before_after", met=True, evidence_quote="invented metrics"),
            CriterionEval(id="learner_contribution", met=True, evidence_quote="invented action"),
            CriterionEval(id="business_or_user_value", met=True, evidence_quote="invented value"),
        ],
        required_missing=[],
        next_focus="Add metrics.",
        pass_eligible=True,
    )
    call_count = 0

    async def invalid_then_timeout(_prompt, _schema):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return first
        raise TimeoutError("repair unavailable")

    monkeypatch.setattr(calls, "_local", lambda: True)
    monkeypatch.setattr(calls, "ollama_structured", invalid_then_timeout)
    state = svc._new_state(
        "user-1",
        "session-int08-quantified-fallback",
        "int_08_quantify_impact",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": (
            "Today we'll focus on quantifying your impact in technical discussions by turning "
            "vague contributions into concrete numbers and measurable outcomes. When you mentioned "
            "optimizing payment flows at your previous role, can you provide a before-and-after "
            "comparison or numerical improvements that came from those efforts?"
        ),
    }, {
        "role": "user",
        "content": answer,
    }, {
        "role": "assistant",
        "content": "I couldn't review that answer reliably, so I haven't counted it. Please send the same answer once more.",
    }]
    for _ in range(3):
        state["messages"].extend([
            {"role": "user", "content": answer},
            {
                "role": "assistant",
                "content": (
                    "I couldn't review that answer reliably, so I haven't counted it. "
                    "Please send the same answer once more."
                ),
            },
        ])

    result = _run(calls.evaluate_prep_answer(
        svc.get_node("int_08_quantify_impact"),
        state["messages"],
        answer,
        state=state,
    ))

    assert call_count == 2
    assert result.pass_eligible is True
    assert result.required_missing == []
    assert result.effective_score == 0.7
    assert all("invented" not in row.evidence_quote for row in result.criteria)


@pytest.mark.parametrize(
    "answer",
    [
        "I ate 3 apples before lunch and 5 apples after lunch, then bought 2 more for tomorrow.",
        (
            "For the payment flow, I ate 3 apples before lunch and 5 apples after lunch. "
            "I introduced a grocery list, and my apple count increased from 3 to 5."
        ),
        (
            "For the payment flow, status latency fell from 18 seconds to 4 seconds and support "
            "tickets dropped from 20 to 8. I introduced a weekly team lunch calendar."
        ),
        (
            "Payment status latency fell from 18 seconds to 4 seconds and support tickets fell 42%, "
            "but I have not explained what I personally changed."
        ),
    ],
)
def test_int08_deterministic_repair_does_not_credit_unrelated_or_actionless_metrics(answer):
    state = svc._new_state(
        "user-1",
        "session-int08-negative-fallback",
        "int_08_quantify_impact",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [{
        "role": "assistant",
        "content": "For the payment flow you optimized, give a before-and-after numerical comparison.",
    }]
    packet = build_evaluation_packet(state, svc.get_node("int_08_quantify_impact"), answer)
    raw = PrepRubricEval(
        raw_score=0.0,
        criteria=[],
        required_missing=["impact_claim", "quantified_before_after", "learner_contribution"],
        next_focus="Add grounded impact proof.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    assert result.required_missing or result.blockers


def test_int08_pass_feedback_names_learner_action_and_metrics_without_generic_praise():
    state = svc._new_state(
        "user-1",
        "session-int08-feedback",
        "int_08_quantify_impact",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": (
            "I introduced idempotency keys; duplicate holds fell from 3.2% to 0.2%, "
            "and support tickets decreased by 42%."
        ),
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "independent",
            "criteria": [
                {
                    "id": "quantified_before_after",
                    "met": True,
                    "evidence_quote": "duplicate holds fell from 3.2% to 0.2%",
                },
                {
                    "id": "learner_contribution",
                    "met": True,
                    "evidence_quote": "I introduced idempotency keys",
                },
            ],
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_fresh_independent",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "That answer is on the right track. Try another example.",
        state,
        "teach",
    )

    assert "I introduced idempotency keys" in cleaned
    assert "duplicate holds fell from 3.2% to 0.2%" in cleaned
    assert "different achievement" in cleaned.lower()
    assert "on the right track" not in cleaned.lower()


def test_int08_partial_feedback_names_only_missing_learner_contribution():
    state = svc._new_state(
        "user-1",
        "session-int08-partial-feedback",
        "int_08_quantify_impact",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": "Status latency fell from 18 seconds to 4 seconds.",
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["learner_contribution"],
            "blockers": ["missing_required:learner_contribution"],
            "attempt_type": "independent",
            "criteria": [
                {
                    "id": "quantified_before_after",
                    "met": True,
                    "evidence_quote": "Status latency fell from 18 seconds to 4 seconds",
                },
                {"id": "learner_contribution", "met": False, "evidence_quote": ""},
            ],
        },
        "tutor_turn_plan": {
            "verdict": "partial",
            "next_action": "rewrite",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "Great job. Add more numbers and try remote work.",
        state,
        "teach",
    )

    assert "18 seconds to 4 seconds" in cleaned
    assert "what you changed" in cleaned.lower()
    assert "more numbers" not in cleaned.lower()
    assert "remote work" not in cleaned.lower()
    assert "great job" not in cleaned.lower()


def test_int08_feedback_never_repeats_quote_from_unmet_criterion():
    state = svc._new_state(
        "user-1",
        "session-int08-unmet-quote",
        "int_08_quantify_impact",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": "I changed the workflow but did not provide a verified metric.",
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["quantified_before_after"],
            "blockers": ["missing_required:quantified_before_after"],
            "attempt_type": "independent",
            "criteria": [
                {
                    "id": "quantified_before_after",
                    "met": False,
                    "evidence_quote": "Revenue increased by 900% at Acme",
                },
                {
                    "id": "learner_contribution",
                    "met": True,
                    "evidence_quote": "I changed the workflow",
                },
            ],
        },
        "tutor_turn_plan": {
            "verdict": "partial",
            "next_action": "rewrite",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response("Use the fabricated metric.", state, "teach")

    assert "900%" not in cleaned
    assert "baseline and a measurable result" in cleaned.lower()


def _late_feedback_state(node_id, task_type, answer, criteria):
    state = svc._new_state(
        "user-1",
        f"session-{node_id}-display-evidence",
        node_id,
        [],
        task_type=task_type,
        career_context=(
            {"gd_topics": ["Should remote work be the default?"]}
            if task_type == "gd_prep"
            else None
        ),
    )
    state.update({
        "user_input": answer,
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "independent",
            "criteria": criteria,
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_fresh_independent",
            "allowed_praise": False,
        },
    })
    if task_type == "gd_prep":
        state["active_gd_prompt_topic"] = "Should remote work be the default?"
    return state


@pytest.mark.parametrize(
    ("node_id", "first_id", "first_sentence", "salient_id", "salient_sentence", "acknowledgement", "task"),
    [
        (
            "gd_06_balanced_view", "names_both_sides",
            "Remote work improves access while office work supports faster onboarding",
            "weighs_tradeoff",
            "The decisive trade-off is access versus onboarding, so hybrid work is the better recommendation",
            "You identified the decisive trade-off", "use a different trade-off",
        ),
        (
            "gd_07_steer_back", "identifies_derailment",
            "We have moved into personal commuting preferences", "gives_next_step",
            "The next useful step is to compare onboarding outcomes under each policy",
            "You gave the group a concrete next step", "group drifts into personal preferences",
        ),
        (
            "gd_08_include_quiet", "names_quiet_participant",
            "Maya, we have not heard from you yet", "topic_linked_invite",
            "Could you share how this policy might affect first-year employees",
            "You linked the invitation to the active motion", "Maya has not spoken",
        ),
        (
            "gd_09_manage_dominator", "acknowledges_contribution",
            "Rohan, your point about delivery speed is useful", "redistributes_floor",
            "Let us hear Maya's view on the implementation risk before returning to this point",
            "You redistributed the floor explicitly", "Rohan interrupts",
        ),
        (
            "gd_10_drive_consensus", "summarizes_key_points",
            "Maya supports the motion while Dev wants stronger evidence", "proposes_next_step",
            "We should adopt a pilot only if it meets the agreed accuracy threshold",
            "You proposed a concrete way forward", "Maya says the evidence supports",
        ),
    ],
)
def test_late_gd_feedback_prefers_node_salient_evidence_and_keeps_next_task(
    node_id, first_id, first_sentence, salient_id, salient_sentence, acknowledgement, task,
):
    state = _late_feedback_state(
        node_id,
        "gd_prep",
        f"{first_sentence}. {salient_sentence}.",
        [
            {"id": first_id, "met": True, "evidence_quote": first_sentence},
            {"id": salient_id, "met": True, "evidence_quote": salient_sentence},
        ],
    )

    feedback = svc._late_gd_feedback_text(state)

    assert f'"{salient_sentence}."' in feedback
    assert f'"{first_sentence}."' not in feedback
    assert acknowledgement in feedback
    assert "The required discussion move is present" not in feedback
    assert task in feedback
    assert state["pending_prompt_attempt_type"] == "independent"


def test_late_gd_long_evidence_displays_one_complete_exact_learner_sentence():
    opening = (
        "The decisive trade-off is broader hiring access versus reliable onboarding, "
        "so I recommend a hybrid policy"
    )
    tail = (
        "I would review that policy after two quarters using retention, manager response time, "
        "new-hire confidence, mentoring coverage, and delivery predictability across every team "
        "before deciding whether any role should move further toward remote or office work."
    )
    answer = f"{opening}. {tail}"
    assert len(answer) > 220
    state = _late_feedback_state(
        "gd_06_balanced_view",
        "gd_prep",
        answer,
        [{"id": "weighs_tradeoff", "met": True, "evidence_quote": opening}],
    )

    feedback = svc._late_gd_feedback_text(state)

    assert f'"{opening}."' in feedback
    assert "mentoring coverage" not in feedback
    assert "The required discussion move is present" not in feedback


def test_late_gd_feedback_omits_evidence_without_grounded_complete_excerpt():
    grounded_but_too_long = " ".join(
        ["Maya could connect first-year employee retention to remote onboarding"] * 5
    )
    cases = (
        (
            "Maya, would you like to add the perspective of first-year employees?",
            "Could you share the customer impact?",
        ),
        (grounded_but_too_long, grounded_but_too_long),
    )
    for answer, evidence_quote in cases:
        state = _late_feedback_state(
            "gd_08_include_quiet",
            "gd_prep",
            answer,
            [{
                "id": "topic_linked_invite",
                "met": True,
                "evidence_quote": evidence_quote,
            }],
        )

        feedback = svc._late_gd_feedback_text(state)

        assert "You linked the invitation to the active motion." in feedback
        assert evidence_quote not in feedback
        assert "includes this evidence" not in feedback


def test_late_gd_feedback_does_not_claim_an_unmet_salient_move():
    state = _late_feedback_state(
        "gd_10_drive_consensus",
        "gd_prep",
        "I support a guarded remote-work policy.",
        [{"id": "proposes_next_step", "met": True, "evidence_quote": "guarded remote-work policy"}],
    )
    state["last_rubric_result"].update({
        "pass_eligible": False,
        "required_missing": ["proposes_next_step"],
    })

    feedback = svc._late_gd_feedback_text(state)

    assert "You proposed a concrete way forward" not in feedback
    assert "You named the common ground" not in feedback
    assert "The missing move is to" in feedback


def test_manage_dominator_reconciles_grounded_respectful_boundary():
    answer = (
        "Rohan, your access point is useful; let me pause you there. "
        "On making remote work the default, let us hear Maya's view on the mentoring risk."
    )
    state = svc._new_state(
        "user-1",
        "session-gd09-boundary",
        "gd_09_manage_dominator",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_09_manage_dominator"), answer)
    missing = [
        "acknowledges_contribution",
        "respectful_boundary",
        "redistributes_floor",
        "topic_link",
    ]
    raw = PrepRubricEval(
        raw_score=0.3,
        criteria=[CriterionEval(id=item, met=False, evidence_quote="") for item in missing],
        required_missing=missing,
        next_focus="Try again.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is True
    assert result.required_missing == []
    assert {row.id for row in result.criteria if row.met} >= set(missing)


def test_manage_dominator_recognizes_dynamic_names_and_natural_boundary():
    prompt = (
        'On "Should remote work be the default?", Ravi keeps interrupting while '
        "Maya has not had a chance to contribute. Set a calm boundary and redistribute the floor."
    )
    claims = svc._gd_task_participant_claims("gd_09_manage_dominator", prompt)
    state = svc._new_state(
        "user-1",
        "session-gd09-dynamic-boundary",
        "gd_09_manage_dominator",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["active_task_contract"] = svc._derived_career_task_payload(
        state,
        {
            "node_id": "gd_09_manage_dominator",
            "content": prompt,
            "message_kind": "coach_response",
        },
    )
    state["active_task_contract"]["prompt_id"] = "gd09-dynamic-prompt"
    answer = (
        "Ravi, please let me finish this point; I will come back to you after Maya "
        "has had a chance to contribute."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_09_manage_dominator"), answer)
    raw = PrepRubricEval(
        raw_score=0.45,
        criteria=[
            CriterionEval(id="respectful_boundary", met=False, evidence_quote=""),
            CriterionEval(id="redistributes_floor", met=False, evidence_quote=""),
            CriterionEval(id="acknowledges_contribution", met=False, evidence_quote=""),
            CriterionEval(id="topic_link", met=False, evidence_quote=""),
        ],
        required_missing=[
            "respectful_boundary",
            "redistributes_floor",
            "acknowledges_contribution",
            "topic_link",
        ],
        next_focus="Set a respectful boundary.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)
    rows = {row.id: row for row in result.criteria}

    assert {claim["display_name"] for claim in claims} >= {"Ravi", "Maya"}
    assert rows["respectful_boundary"].met is True
    assert rows["redistributes_floor"].met is True
    assert rows["acknowledges_contribution"].met is False
    assert rows["topic_link"].met is False
    assert result.pass_eligible is False


def test_manage_dominator_does_not_credit_the_wrong_named_participant():
    prompt = (
        'On "Should remote work be the default?", Ravi keeps interrupting while '
        "Maya has not had a chance to contribute. Set a calm boundary and redistribute the floor."
    )
    state = svc._new_state(
        "user-1",
        "session-gd09-wrong-participant",
        "gd_09_manage_dominator",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["active_task_contract"] = svc._derived_career_task_payload(
        state,
        {
            "node_id": "gd_09_manage_dominator",
            "content": prompt,
            "message_kind": "coach_response",
        },
    )
    state["active_task_contract"]["prompt_id"] = "gd09-wrong-participant-prompt"
    answer = (
        "Rohan, your point about remote-work access is useful; please let me finish this "
        "point. On making remote work the default, give Maya a chance to contribute."
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_09_manage_dominator"), answer)
    missing = [
        "acknowledges_contribution",
        "respectful_boundary",
        "redistributes_floor",
        "topic_link",
    ]
    raw = PrepRubricEval(
        raw_score=0.3,
        criteria=[CriterionEval(id=item, met=False, evidence_quote="") for item in missing],
        required_missing=missing,
        next_focus="Address the assigned dominant participant.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)
    rows = {row.id: row for row in result.criteria}

    assert rows["acknowledges_contribution"].met is False
    assert rows["respectful_boundary"].met is False
    assert rows["redistributes_floor"].met is True
    assert result.pass_eligible is False


@pytest.mark.parametrize(("answer", "has_explicit_boundary"), [
    ((
        "Rohan, your access point is useful and relevant to remote work being the default. "
        "Maya, please take the floor and give us your mentoring perspective."
    ), False),
    ((
        "Remote work is important to company policy, so let's pause here. "
        "Let's hear from Maya about the remote-work mentoring risk before we continue."
    ), False),
    ((
        "Maya, your mentoring perspective is useful. Rohan, let me pause you there. "
        "On making remote work the default, Maya, please take the floor."
    ), True),
    ((
        "Maya, your mentoring perspective is useful, but Rohan, let me pause you there. "
        "On making remote work the default, Maya, please take the floor."
    ), True),
    ((
        "Maya, your mentoring perspective is useful but Rohan, let me pause you there. "
        "On making remote work the default, Maya, please take the floor."
    ), True),
])
def test_manage_dominator_credits_only_an_explicit_boundary(answer, has_explicit_boundary):
    state = svc._new_state(
        "user-1",
        "session-gd09-no-boundary",
        "gd_09_manage_dominator",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    packet = build_evaluation_packet(state, svc.get_node("gd_09_manage_dominator"), answer)
    raw = PrepRubricEval(
        raw_score=0.5,
        criteria=[],
        required_missing=["respectful_boundary"],
        next_focus="Set a respectful boundary.",
        pass_eligible=False,
    )

    result = apply_caps(packet, raw)

    assert result.pass_eligible is False
    boundary = next(row for row in result.criteria if row.id == "respectful_boundary")
    assert boundary.met is has_explicit_boundary


@pytest.mark.parametrize(
    ("node_id", "criterion_id", "opening", "tail", "next_task", "renderer"),
    [
        (
            "int_08_quantify_impact", "quantified_before_after",
            "Deployment failures fell from 14 per quarter to 3 after I introduced staged rollouts",
            "I tracked the result across payment, notification, reconciliation, and reporting services before treating the change as reliable enough for the wider platform.",
            "different achievement", svc._int08_feedback_text,
        ),
        (
            "int_09_diplomatic_pushback", "requirement_based_reasoning",
            "The fair concern is release speed, but recoverability under failed deployments is the governing requirement",
            "I would preserve automated rollback checks, staged exposure, production telemetry, and an explicit owner for the go-or-no-go decision across every release path before accepting a faster manual-only process.",
            "Extensive manual testing", svc._late_interview_feedback_text,
        ),
    ],
)
def test_late_interview_long_evidence_displays_one_complete_exact_learner_sentence(
    node_id, criterion_id, opening, tail, next_task, renderer,
):
    answer = f"{opening}. {tail}"
    assert len(answer) > 220
    state = _late_feedback_state(
        node_id,
        "interview_prep",
        answer,
        [{"id": criterion_id, "met": True, "evidence_quote": opening}],
    )

    feedback = renderer(state)

    assert f'"{opening}."' in feedback
    assert tail not in feedback
    assert next_task in feedback


def test_forged_parent_id_fails_closed_on_pressure_rubric():
    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    state.update({
        "active_prompt_attempt_type": "pressure",
        "core_qualified": True,
        "core_qualification_turn_id": "does-not-exist",
        "core_qualification_evidence": {
            "evaluation_id": "different-id",
            "user_id": "user-1",
            "node_id": "int_03_weakness_framing",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
        },
    })

    packet = build_evaluation_packet(
        state,
        svc.get_node("int_03_weakness_framing"),
        "I would defend the rollout with the measured failure rate.",
    )

    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.9,
            criteria=[
                CriterionEval(id="pressure_response", met=True, evidence_quote="defend the rollout"),
                CriterionEval(id="evidence_defense", met=True, evidence_quote="measured failure rate"),
                CriterionEval(id="core_consistency", met=True, evidence_quote="defend the rollout"),
            ],
            required_missing=[],
            next_focus="Try another objection.",
            pass_eligible=True,
        ),
    )

    assert packet.core_qualified is False
    assert packet.core_qualification_evidence == {}
    assert [criterion["id"] for criterion in packet.criteria] == [
        "pressure_response", "evidence_defense", "core_consistency"
    ]
    assert result.pass_eligible is False
    assert "core_consistency" in result.required_missing


def test_forged_parent_id_fails_closed_on_transfer_rubric():
    state = svc._new_state(
        "user-1", "session-forged-transfer", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    state.update({
        "active_prompt_attempt_type": "transfer",
        "core_qualified": True,
        "core_qualification_turn_id": "does-not-exist",
        "core_qualification_evidence": {
            "evaluation_id": "different-id",
            "user_id": "user-1",
            "node_id": "int_03_weakness_framing",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
        },
    })
    answer = (
        "Earlier I rushed technical details. I now open with decision criteria, and in a payment "
        "rollout that change prevented a rollback and reduced support tickets by 20 percent."
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.9,
            criteria=[
                CriterionEval(id="real_weakness", met=True, evidence_quote="rushed technical details"),
                CriterionEval(id="mitigation_habit", met=True, evidence_quote="open with decision criteria"),
                CriterionEval(id="progress_evidence", met=True, evidence_quote="reduced support tickets by 20 percent"),
                CriterionEval(id="non_self_sabotage", met=True, evidence_quote="I now open with decision criteria"),
                CriterionEval(id="transfer_context", met=True, evidence_quote="payment rollout"),
            ],
            required_missing=[],
            next_focus="Try pressure.",
            pass_eligible=True,
        ),
    )

    assert packet.core_qualified is False
    assert "transfer_context" in [criterion["id"] for criterion in packet.criteria]
    assert result.pass_eligible is False
    assert "transfer_context" in result.required_missing


def test_transfer_with_matching_parent_but_missing_qualified_answer_fails_closed():
    state = svc._new_state(
        "user-1", "session-missing-parent-answer", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    parent_id = "session-missing-parent-answer:core"
    state.update({
        "active_prompt_attempt_type": "transfer",
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "int_03_weakness_framing",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
        },
    })
    answer = (
        "Earlier I rushed technical details. I now open with decision criteria, and in a payment "
        "rollout that change prevented a rollback and reduced support tickets by 20 percent."
    )
    packet = build_evaluation_packet(state, svc.get_node("int_03_weakness_framing"), answer)
    result = apply_caps(
        packet,
        PrepRubricEval(
            raw_score=0.9,
            criteria=[
                CriterionEval(id="real_weakness", met=True, evidence_quote="rushed technical details"),
                CriterionEval(id="mitigation_habit", met=True, evidence_quote="open with decision criteria"),
                CriterionEval(id="progress_evidence", met=True, evidence_quote="reduced support tickets by 20 percent"),
                CriterionEval(id="non_self_sabotage", met=True, evidence_quote="I now open with decision criteria"),
                CriterionEval(id="transfer_context", met=True, evidence_quote="payment rollout"),
            ],
            required_missing=[],
            next_focus="Try pressure.",
            pass_eligible=True,
            mastery_eligible=True,
        ),
    )

    assert packet.core_qualified is False
    assert result.pass_eligible is False
    assert result.mastery_eligible is False
    assert "transfer_context" in result.required_missing


def test_transfer_pass_cannot_create_its_own_core_parent():
    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    state.update({
        "independent_passes": 2,
        "last_eval_score": 0.88,
        "last_clean_pass_score": 0.88,
        "last_diagnosis": {"on_task": True, "english": True},
        "last_rubric_result": {
            "effective_score": 0.88,
            "pass_eligible": True,
            "mastery_eligible": True,
            "attempt_type": "transfer",
            "required_missing": [],
            "blockers": [],
            "criteria": [],
        },
    })

    svc._update_progress(state)

    assert state["core_qualified"] is False
    assert state["core_qualification_turn_id"] is None


def test_existing_session_recovers_core_parent_from_durable_independent_eval(monkeypatch):
    class Store:
        async def get_latest_passing_turn_evaluation(self, user_id, node_id, attempt_type):
            assert (user_id, node_id, attempt_type) == (
                "user-1", "int_03_weakness_framing", "independent"
            )
            return {
                "evaluation_id": "session-old:turn-core-2:int_03_weakness_framing",
                "user_id": user_id,
                "node_id": node_id,
                "attempt_type": attempt_type,
                "pass_eligible": True,
                "blockers": [],
                "effective_score": 0.85,
                "user_answer": (
                    "My weakness was rushing rollouts; I now use phased pilots and decision gates."
                ),
                "context_json": {
                    "task_contract": {
                        "prompt_id": "core-prompt",
                        "context_id": "int_03_weakness_framing:independent:core",
                        "semantic_anchors": [],
                    },
                },
            }

    state = svc._new_state(
        "user-1", "session-1", "int_03_weakness_framing", [], task_type="interview_prep"
    )
    state.update({
        "independent_passes": 4,
        "core_qualified": True,
        "core_qualification_turn_id": "session-old:turn-core-2:int_03_weakness_framing",
        "core_qualification_evidence": {
            "evaluation_id": "session-old:turn-core-2:int_03_weakness_framing",
            "user_id": "user-1",
            "node_id": "int_03_weakness_framing",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": "Legacy answer without a task contract.",
        },
    })
    monkeypatch.setattr(svc, "get_storage", lambda: Store())

    _run(svc._hydrate_core_qualification(state))

    assert state["core_qualified"] is True
    assert state["core_qualification_turn_id"] == (
        "session-old:turn-core-2:int_03_weakness_framing"
    )
    assert state["core_qualification_evidence"]["learner_answer"] == (
        "My weakness was rushing rollouts; I now use phased pilots and decision gates."
    )
    assert state["core_qualification_evidence"]["task_contract"]["context_id"] == (
        "int_03_weakness_framing:independent:core"
    )


def test_gd_core_hydration_preserves_qualified_topic_not_current_session_topic(monkeypatch):
    class Store:
        async def get_latest_passing_turn_evaluation(self, user_id, node_id, attempt_type):
            return {
                "evaluation_id": "session-old:turn-core:gd_05_disagree_respectfully",
                "user_id": user_id,
                "node_id": node_id,
                "attempt_type": attempt_type,
                "pass_eligible": True,
                "blockers": [],
                "effective_score": 0.85,
                "user_answer": (
                    "I agree AI screening can improve consistency, but models can scale "
                    "historical bias without cohort audits."
                ),
                "context_json": {
                    "active_topic": "Should companies use AI in hiring?",
                },
            }

    state = svc._new_state(
        "user-1",
        "session-new-topic",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state.update({
        "independent_passes": 3,
        "messages": [{
            "role": "assistant",
            "node_id": "gd_05_disagree_respectfully",
            "content": "Motion: \"Should remote work be the default?\"",
        }],
    })
    monkeypatch.setattr(svc, "get_storage", lambda: Store())

    _run(svc._hydrate_core_qualification(state))

    assert state["core_qualification_evidence"]["active_topic"] == (
        "Should companies use AI in hiring?"
    )


def test_gd_core_hydration_rejects_legacy_evaluation_without_persisted_topic(monkeypatch):
    class Store:
        async def get_latest_passing_turn_evaluation(self, user_id, node_id, attempt_type):
            return {
                "evaluation_id": "session-old:turn-core:gd_05_disagree_respectfully",
                "user_id": user_id,
                "node_id": node_id,
                "attempt_type": attempt_type,
                "pass_eligible": True,
                "blockers": [],
                "effective_score": 0.85,
                "user_answer": "I agree AI screening can help, but models can scale bias.",
                "context_json": {},
            }

    state = svc._new_state(
        "user-1",
        "session-new-topic-legacy",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["independent_passes"] = 3
    monkeypatch.setattr(svc, "get_storage", lambda: Store())

    _run(svc._hydrate_core_qualification(state))

    assert state["core_qualified"] is False
    assert state["core_qualification_evidence"] is None


def test_gd_core_hydration_clears_legacy_runtime_snapshot_without_topic(monkeypatch):
    class Store:
        async def get_latest_passing_turn_evaluation(self, user_id, node_id, attempt_type):
            return {
                "evaluation_id": "session-old:turn-core:gd_05_disagree_respectfully",
                "user_id": user_id,
                "node_id": node_id,
                "attempt_type": attempt_type,
                "pass_eligible": True,
                "blockers": [],
                "effective_score": 0.85,
                "user_answer": "I agree AI screening can help, but models can scale bias.",
                "context_json": {},
            }

    state = svc._new_state(
        "user-1",
        "session-legacy-runtime-topic",
        "gd_05_disagree_respectfully",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    parent_id = "session-old:turn-core:gd_05_disagree_respectfully"
    state.update({
        "independent_passes": 3,
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": "user-1",
            "node_id": "gd_05_disagree_respectfully",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": "I agree AI screening can help, but models can scale bias.",
        },
        "messages": [{
            "role": "assistant",
            "node_id": "gd_05_disagree_respectfully",
            "content": "Motion: \"Should remote work be the default?\"",
        }],
    })
    monkeypatch.setattr(svc, "get_storage", lambda: Store())

    _run(svc._hydrate_core_qualification(state))

    assert state["core_qualified"] is False
    assert state["core_qualification_turn_id"] is None
    assert state["core_qualification_evidence"] is None


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
        "I think AI is useful.",
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
    assert "learner-owned evidence" in plan.focus


def test_tutor_plan_escalates_repeated_hot_gap_without_mastery_praise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
    )
    state["session_learning_delta"] = {
        "strengths": [],
        "active_gaps": ["Add the result or measurable impact."],
        "repeated_issue_counts": {"criterion:result": 1},
        "growth_signals": [],
        "resolved_candidates": [],
        "latest_evidence_quotes": ["In a payment outage, I traced retries."],
    }
    result = {
        "english": True,
        "on_task": True,
        "required_missing": ["result"],
        "pass_eligible": False,
        "mastery_eligible": False,
        "next_focus": "Show the business impact.",
    }

    plan = build_tutor_turn_plan(result, state)

    assert plan.verdict == "repeat_gap"
    assert plan.next_action == "micro_drill_then_rewrite"
    assert plan.allowed_praise is False
    assert plan.tone_policy == "direct_no_praise_supportive"
    assert "repeated 2x this session" in plan.focus


def test_hot_session_delta_records_missing_criterion_repeat_keys(store):
    state = svc._new_state(
        "user-1",
        "session-hot-delta-criterion",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["user_input"] = "In a payment outage, I traced retries and shipped a fix."
    state["last_eval_score"] = 0.49
    state["last_diagnosis"] = {"on_task": True, "english": True, "affect": "neutral", "next_focus": "Add the measurable result."}
    state["last_rubric_result"] = {
        "raw_score": 0.49,
        "effective_score": 0.49,
        "strengths": ["specific situation"],
        "next_focus": "Add the measurable result.",
        "required_missing": ["result"],
        "criteria": [{"id": "result", "met": False, "evidence_quote": ""}],
        "blockers": ["missing_required:result"],
        "pass_eligible": False,
        "mastery_eligible": False,
        "attempt_type": "independent",
    }
    state["tutor_turn_plan"] = {"next_action": "rewrite"}

    _run(svc._track_turn(state, "int_04_star_behavioral"))

    repeated = state["session_learning_delta"]["repeated_issue_counts"]
    assert repeated["Add the measurable result."] == 1
    assert repeated["criterion:result"] == 1
    assert state["session_learning_delta"]["task_type"] == "interview_prep"
    assert state["session_learning_delta"]["module_id"] == "interview"


def test_tutor_plan_disallows_celebratory_praise_for_scaffolded_and_borderline_passes():
    scaffolded_plan = build_tutor_turn_plan(
        {
            "english": True,
            "on_task": True,
            "required_missing": [],
            "pass_eligible": True,
            "mastery_eligible": False,
            "next_focus": "Try it without the scaffold.",
        },
        {},
        scaffolded=True,
    )
    borderline_plan = build_tutor_turn_plan(
        {
            "english": True,
            "on_task": True,
            "required_missing": [],
            "pass_eligible": True,
            "mastery_eligible": False,
            "next_focus": "Make the answer more concrete.",
        },
        {},
    )

    assert scaffolded_plan.allowed_praise is False
    assert scaffolded_plan.tone_policy == "warm_but_not_mastery"
    assert borderline_plan.allowed_praise is False
    assert borderline_plan.tone_policy == "measured_no_celebration"


@pytest.mark.parametrize(
    ("attempt_type", "counters", "expected_marker", "expected_kind"),
    [
        ("independent", {"independent_passes": 0}, "independent", "fresh_independent"),
        ("independent", {"independent_passes": 1}, "transfer", "transfer"),
        ("transfer", {"transfer_passes": 0, "core_qualified": True}, "pressure", "pressure"),
        ("pressure", {"pressure_passes": 0, "core_qualified": True}, "independent", "consolidation"),
    ],
)
def test_int01_next_task_decision_projects_the_current_clean_pass(
    attempt_type, counters, expected_marker, expected_kind
):
    state = svc._new_state(
        "user-1",
        "session-int01-decision",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state.update(counters)
    if state.get("core_qualified"):
        parent_id = "session-int01-decision:turn-core:int_01_elevator_pitch"
        state.update({
            "core_qualification_turn_id": parent_id,
            "core_qualification_evidence": {
                "evaluation_id": parent_id,
                "user_id": "user-1",
                "node_id": "int_01_elevator_pitch",
                "attempt_type": "independent",
                "pass_eligible": True,
                "blockers": [],
                "learner_answer": "I am a backend engineer who improved payment reliability.",
            },
        })
    result = {
        "english": True,
        "on_task": True,
        "pass_eligible": True,
        "mastery_eligible": False,
        "required_missing": [],
        "blockers": [],
        "attempt_type": attempt_type,
        "next_focus": "Make the current pitch more measurable.",
    }

    decision = decide_int01_next_task(result, state)

    assert decision is not None
    assert decision.attempt_type == expected_marker
    assert decision.kind == expected_kind


def test_clean_int01_tutor_plan_never_tightens_or_repeats_a_deficit():
    state = svc._new_state(
        "user-1",
        "session-int01-plan",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state["independent_passes"] = 1
    result = {
        "english": True,
        "on_task": True,
        "pass_eligible": True,
        "mastery_eligible": False,
        "required_missing": [],
        "blockers": [],
        "attempt_type": "independent",
        "next_focus": "Add missing evidence and make the pitch more measurable.",
    }

    plan = build_tutor_turn_plan(result, state)

    assert plan.next_action == "request_transfer"
    assert plan.focus == "use a different achievement for a different audience"
    assert "gap" not in plan.focus.lower()
    assert "missing" not in plan.focus.lower()
    assert "measurable" not in plan.focus.lower()


def test_clean_star_tutor_plan_requests_transfer_instead_of_inventing_a_gap():
    state = svc._new_state(
        "user-1",
        "session-star-plan",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
    )
    state["independent_passes"] = 1
    result = {
        "english": True,
        "on_task": True,
        "pass_eligible": True,
        "mastery_eligible": False,
        "required_missing": [],
        "blockers": [],
        "attempt_type": "independent",
        "next_focus": "Add broader business impact even though it is already present.",
    }

    plan = build_tutor_turn_plan(result, state)

    assert plan.verdict == "independent_pass"
    assert plan.next_action == "request_transfer"
    assert plan.focus == "apply the same skill in a meaningfully different realistic context"
    assert "gap" not in plan.focus.lower()


def test_clean_star_feedback_rejects_false_missing_impact_and_sets_transfer_task():
    answer = (
        "In a payments platform migration, webhook retries caused duplicate writes. "
        "I owned reliability, added idempotency keys, batched writes, and staged rollout. "
        "Duplicate writes fell 96%, latency dropped from 18 seconds to 4, and support "
        "tickets declined 31%, protecting merchant trust and reducing support load."
    )
    state = svc._new_state(
        "user-1",
        "session-star-feedback",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": answer,
        "independent_passes": 1,
        "last_rubric_result": {
            "pass_eligible": True,
            "mastery_eligible": False,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "independent",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_transfer",
            "tone_policy": "measured_forward",
            "allowed_praise": False,
            "focus": "apply the same skill in a meaningfully different realistic context",
            "stage": "challenge",
        },
    })
    offending = (
        "Your response has measurable improvements. To elevate it further, describe how "
        "these optimizations impacted user experience and business metrics beyond the "
        "technical outcomes."
    )

    cleaned = svc._sanitize_coaching_response(offending, state, "teach")

    assert "beyond" not in cleaned.lower()
    assert "all star parts are present" in cleaned.lower()
    assert "different star story" in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "transfer"


def test_clean_star_transfer_to_pressure_names_the_qualified_core_story():
    core_answer = (
        "During a payment migration, I owned the retry redesign, introduced idempotency, "
        "and reduced duplicate writes by 96 percent."
    )
    transfer_answer = (
        "During an analytics outage, I rebuilt the ingestion queue and cut recovery time in half."
    )
    state = svc._new_state(
        "user-1",
        "session-star-pressure-parent",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": transfer_answer,
        "core_qualified": True,
        "core_qualification_turn_id": "star-core-evaluation",
        "core_qualification_evidence": {
            "evaluation_id": "star-core-evaluation",
            "user_id": "user-1",
            "node_id": "int_04_star_behavioral",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": core_answer,
            "active_topic": "",
        },
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_pressure",
            "tone_policy": "stretch",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response(
        "Defend the analytics story you just gave.",
        state,
        "challenge",
    )
    pressure_task = cleaned.lower().split("next task:", 1)[1]

    assert "earlier star story" in pressure_task
    assert "payment migration" in pressure_task
    assert "analytics outage" not in pressure_task
    assert state["pending_prompt_attempt_type"] == "pressure"


def test_clean_star_invalid_core_parent_cannot_stage_pressure():
    state = svc._new_state(
        "user-1",
        "session-star-invalid-pressure-parent",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": "I gave a complete transfer STAR answer with a measurable result.",
        "core_qualified": False,
        "core_qualification_turn_id": None,
        "core_qualification_evidence": None,
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_pressure",
            "tone_policy": "stretch",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response("Defend the same story.", state, "challenge")

    assert "new star story" in cleaned.lower()
    assert "before i challenge" in cleaned.lower()
    assert "skeptical interviewer" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def _int06_feedback_state(*, next_action: str = "request_fresh_independent") -> dict:
    answer = (
        "I approved the migration without a rollback rehearsal. The release delayed "
        "merchant payouts for two hours. I paused the rollout and reconciled every "
        "affected payout. Afterward, I required rollback rehearsals before migrations."
    )
    state = svc._new_state(
        "user-1",
        f"session-int06-{next_action}",
        "int_06_own_a_failure",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": answer,
        "core_qualified": True,
        "core_qualification_turn_id": "int06-core-evaluation",
        "core_qualification_evidence": {
            "evaluation_id": "int06-core-evaluation",
            "user_id": "user-1",
            "node_id": "int_06_own_a_failure",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": answer,
            "active_topic": "",
        },
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "independent",
            "criteria": [
                {
                    "id": "ownership",
                    "met": True,
                    "evidence_quote": "I approved the migration without a rollback rehearsal",
                },
                {
                    "id": "impact",
                    "met": True,
                    "evidence_quote": "delayed merchant payouts for two hours",
                },
                {
                    "id": "response_action",
                    "met": True,
                    "evidence_quote": "paused the rollout and reconciled every affected payout",
                },
                {
                    "id": "prevention",
                    "met": True,
                    "evidence_quote": "required rollback rehearsals before migrations",
                },
                {"id": "non_defensive_tone", "met": True, "evidence_quote": "I approved"},
            ],
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": next_action,
            "tone_policy": "measured_no_celebration",
            "allowed_praise": False,
        },
    })
    return state


def test_int06_clean_pass_feedback_uses_validated_proof_and_requests_one_fresh_incident():
    state = _int06_feedback_state()
    offending = (
        "Outstanding answer. At Acme, your outage cut revenue by 40%, so you have "
        "mastered failure stories. Here is a sample answer you can use."
    )

    cleaned = svc._sanitize_coaching_response(offending, state, "teach")
    lowered = cleaned.lower()

    for proof in (
        "I approved the migration without a rollback rehearsal",
        "delayed merchant payouts for two hours",
        "paused the rollout and reconciled every affected payout",
        "required rollback rehearsals before migrations",
    ):
        assert proof in cleaned
    assert "all four required parts are present" in lowered
    assert "no content gap" in lowered
    assert "exactly one different incident from your own experience" in lowered
    assert "different cause" in lowered
    assert "ownership, impact, immediate response, and prevention" in lowered
    for invented_or_inflated in ("acme", "40%", "outstanding", "mastered", "sample answer"):
        assert invented_or_inflated not in lowered
    assert state["pending_prompt_attempt_type"] == "independent"


def test_int06_transfer_feedback_requests_one_meaningful_constraint_and_sets_transfer():
    state = _int06_feedback_state(next_action="request_transfer")

    cleaned = svc._sanitize_coaching_response(
        "Perfect. Invent a stronger metric and use a bigger employer.",
        state,
        "teach",
    )
    lowered = cleaned.lower()

    assert "one meaningful constraint" in lowered
    assert "ownership, impact, immediate response, and prevention" in lowered
    assert "invent a stronger metric" not in lowered
    assert "bigger employer" not in lowered
    assert "perfect" not in lowered
    assert state["pending_prompt_attempt_type"] == "transfer"


def test_int06_missing_required_criterion_gets_targeted_repair_not_completeness():
    state = _int06_feedback_state()
    state["last_rubric_result"].update({
        "pass_eligible": False,
        "required_missing": ["response_action"],
        "blockers": ["missing_required:response_action"],
    })
    for criterion in state["last_rubric_result"]["criteria"]:
        if criterion["id"] == "response_action":
            criterion.update({"met": False, "evidence_quote": ""})

    cleaned = svc._sanitize_coaching_response(
        "Everything is complete. You have mastered the answer.",
        state,
        "teach",
    )
    lowered = cleaned.lower()

    assert "missing required part is the immediate response or repair action" in lowered
    assert "add only that missing part" in lowered
    assert "all four required parts are present" not in lowered
    assert "no content gap" not in lowered
    assert "mastered" not in lowered
    assert state["pending_prompt_attempt_type"] is None


def test_int06_missing_criterion_acknowledges_only_validated_existing_proof():
    state = _int06_feedback_state()
    state["last_rubric_result"].update({
        "pass_eligible": False,
        "required_missing": ["response_action"],
        "blockers": ["missing_required:response_action"],
    })
    for criterion in state["last_rubric_result"]["criteria"]:
        if criterion["id"] == "response_action":
            criterion.update({"met": False, "evidence_quote": ""})

    cleaned = svc._sanitize_coaching_response(
        "Excellent. Everything is already covered.",
        state,
        "teach",
    )

    assert "I approved the migration without a rollback rehearsal" in cleaned
    assert "delayed merchant payouts for two hours" in cleaned
    assert "required rollback rehearsals before migrations" in cleaned
    assert "paused the rollout and reconciled every affected payout" not in cleaned
    assert "missing required part is the immediate response or repair action" in cleaned.lower()
    assert "add only that missing part" in cleaned.lower()


def test_int06_pressure_feedback_uses_same_incident_and_sets_pressure_attempt():
    state = _int06_feedback_state(next_action="request_pressure")
    state["user_input"] = (
        "I approved a cache change during a freeze. Checkout latency rose for 20 minutes. "
        "I disabled the feature flag and warmed the old keys. Afterward I required cache replays."
    )
    state["last_rubric_result"].update({"attempt_type": "transfer"})
    evidence_by_id = {
        "ownership": "I approved a cache change during a freeze",
        "impact": "Checkout latency rose for 20 minutes",
        "response_action": "I disabled the feature flag and warmed the old keys",
        "prevention": "Afterward I required cache replays",
    }
    for criterion in state["last_rubric_result"]["criteria"]:
        if criterion["id"] in evidence_by_id:
            criterion["evidence_quote"] = evidence_by_id[criterion["id"]]

    cleaned = svc._sanitize_coaching_response(
        "Perfect. Invent a more impressive failure for the next round.",
        state,
        "teach",
    )
    lowered = cleaned.lower()
    pressure_task = lowered.split("pressure task:", 1)[1]

    assert "qualified incident" in lowered
    assert "i approved the migration without a rollback rehearsal" in lowered
    assert "cache change during a freeze" not in pressure_task
    assert "interviewer" in lowered
    assert "pushback" in lowered
    assert "do not invent a new story" in lowered
    assert state["pending_prompt_attempt_type"] == "pressure"
    assert "perfect" not in lowered


def test_int06_partial_pressure_feedback_uses_pressure_criteria_and_core_parent_only():
    state = _int06_feedback_state()
    state["user_input"] = (
        "You should trust my judgment because I reported the failure immediately. "
        "I chose the safest available response and documented the decision."
    )
    state["last_rubric_result"] = {
        "pass_eligible": False,
        "required_missing": ["core_consistency"],
        "blockers": ["missing_required:core_consistency"],
        "attempt_type": "pressure",
        "criteria": [
            {
                "id": "pressure_response",
                "met": True,
                "evidence_quote": "You should trust my judgment because I reported the failure immediately.",
            },
            {
                "id": "evidence_defense",
                "met": True,
                "evidence_quote": "I chose the safest available response and documented the decision.",
            },
            {"id": "core_consistency", "met": False, "evidence_quote": ""},
        ],
    }
    state["tutor_turn_plan"] = {
        "verdict": "partial",
        "next_action": "rewrite",
        "tone_policy": "direct_no_praise",
        "allowed_praise": False,
    }

    cleaned = svc._sanitize_coaching_response(
        "Everything is missing. Retell all four parts.",
        state,
        "teach",
    )
    lowered = cleaned.lower()

    assert "reported the failure immediately" in lowered
    assert "safest available response" in lowered
    assert "missing pressure proof is consistency with the qualified incident" in lowered
    assert "i approved the migration without a rollback rehearsal" in lowered
    assert "first-person ownership without blame" not in lowered
    assert "user, customer, business, or team impact" not in lowered
    assert state["pending_prompt_attempt_type"] == "pressure"


def test_int06_passing_pressure_feedback_consolidates_the_qualified_incident():
    state = _int06_feedback_state(next_action="request_consolidation")
    state["user_input"] = (
        "You should trust my judgment because I owned the migration decision. "
        "The payout delay showed the risk, and rollback rehearsals prevent a repeat."
    )
    state["last_rubric_result"] = {
        "pass_eligible": True,
        "required_missing": [],
        "blockers": [],
        "attempt_type": "pressure",
        "criteria": [
            {
                "id": "pressure_response",
                "met": True,
                "evidence_quote": "You should trust my judgment because I owned the migration decision.",
            },
            {
                "id": "evidence_defense",
                "met": True,
                "evidence_quote": "The payout delay showed the risk, and rollback rehearsals prevent a repeat.",
            },
            {
                "id": "core_consistency",
                "met": True,
                "evidence_quote": "I owned the migration decision.",
            },
        ],
    }
    state["tutor_turn_plan"] = {
        "verdict": "independent_pass",
        "next_action": "request_consolidation",
        "tone_policy": "measured_forward",
        "allowed_praise": False,
    }

    cleaned = svc._sanitize_coaching_response(
        "Perfect. You mastered this; use a sample story next.",
        state,
        "teach",
    )
    lowered = cleaned.lower()

    assert "pressure answer provides this proof" in lowered
    assert "qualified incident" in lowered
    assert "i approved the migration without a rollback rehearsal" in lowered
    assert "final delivery" in lowered
    assert state["pending_prompt_attempt_type"] == "independent"
    for forbidden in ("perfect", "mastered", "sample story", "all four required parts"):
        assert forbidden not in lowered


def test_int06_consolidation_feedback_preserves_proven_facts_and_sets_independent_attempt():
    state = _int06_feedback_state(next_action="request_consolidation")

    cleaned = svc._sanitize_coaching_response(
        "You have mastered this. Replace the facts with a cleaner sample answer.",
        state,
        "teach",
    )
    lowered = cleaned.lower()

    assert "final delivery" in lowered
    assert "same proven incident" in lowered
    assert "without changing any facts" in lowered
    assert "ownership, impact, immediate response, and prevention" in lowered
    assert state["pending_prompt_attempt_type"] == "independent"
    assert "mastered" not in lowered
    assert "sample answer" not in lowered


def test_int06_unknown_clean_pass_action_fails_closed_to_learner_anchored_delivery():
    state = _int06_feedback_state(next_action="unexpected_action")

    cleaned = svc._sanitize_coaching_response(
        "Outstanding. At Acme you lost $4m; use that invented example.",
        state,
        "teach",
    )
    lowered = cleaned.lower()

    assert "I approved the migration without a rollback rehearsal" in cleaned
    assert "keep this incident and its facts unchanged" in lowered
    assert "ownership, impact, immediate response, and prevention" in lowered
    assert state["pending_prompt_attempt_type"] == "independent"
    for forbidden in ("outstanding", "acme", "$4m", "invented example"):
        assert forbidden not in lowered


def test_int06_feedback_is_strictly_scoped_away_from_other_nodes_and_test_tasks():
    wrong_node = _int06_feedback_state()
    wrong_node["competency_node"] = "gd_02_support_with_evidence"
    interview_test = _int06_feedback_state()
    interview_test["task_type"] = "interview_test"
    gd_task = _int06_feedback_state()
    gd_task["task_type"] = "gd_prep"

    assert svc._int06_feedback_text(wrong_node) is None
    assert svc._int06_feedback_text(interview_test) is None
    assert svc._int06_feedback_text(gd_task) is None


def test_int06_invalid_core_parent_cannot_stage_pressure_from_corrupt_plan():
    state = _int06_feedback_state(next_action="request_pressure")
    state.update({
        "core_qualified": False,
        "core_qualification_turn_id": None,
        "core_qualification_evidence": None,
    })

    cleaned = svc._sanitize_coaching_response(
        "Pressure task: defend the transfer story.",
        state,
        "challenge",
    )

    assert "new failure story" in cleaned.lower()
    assert "before i challenge" in cleaned.lower()
    assert "why should i trust your judgment" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_int06_active_pressure_without_core_parent_requalifies_independently():
    state = _int06_feedback_state(next_action="rewrite")
    state.update({
        "core_qualified": False,
        "core_qualification_turn_id": None,
        "core_qualification_evidence": None,
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["core_consistency"],
            "blockers": ["missing_required:core_consistency"],
            "attempt_type": "pressure",
            "criteria": [
                {"id": "pressure_response", "met": True, "evidence_quote": "I owned the decision"},
                {"id": "evidence_defense", "met": True, "evidence_quote": "I changed the process"},
                {"id": "core_consistency", "met": False, "evidence_quote": ""},
            ],
        },
    })
    state["user_input"] = "I owned the decision and I changed the process."

    cleaned = svc._sanitize_coaching_response("Retry the pressure answer.", state, "challenge")

    assert "new failure story" in cleaned.lower()
    assert "cannot fairly continue" in cleaned.lower()
    assert "same pushback" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_why_company_opening_requires_a_named_real_company_without_assuming_one():
    state = svc._new_state(
        "user-1",
        "session-why-company-opening",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
        career_context={
            "primary_role": "Backend Software Engineer",
            "target_roles": ["Backend Software Engineer", "Platform Engineer"],
            "role_family": "software_technical",
        },
    )

    opening = svc._int05_opening_text(state)

    assert "Backend Software Engineer" in opening
    assert "choose a company" in opening.lower()
    assert "verified" in opening.lower()
    assert "this company" not in opening.lower()
    assert "Platform Engineer" not in opening


def test_clean_why_company_feedback_preserves_learner_company_and_primary_role():
    answer = (
        "Stripe's developer-first APIs and programmable billing infrastructure attract me. "
        "I have built idempotent payment and usage-metering systems, so this Backend "
        "Software Engineer role fits the work I want to deepen."
    )
    state = svc._new_state(
        "user-1",
        "session-why-company-pass",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
        career_context={
            "primary_role": "Backend Software Engineer",
            "target_roles": ["Backend Software Engineer", "Platform Engineer"],
            "role_family": "software_technical",
        },
    )
    state.update({
        "user_input": answer,
        "last_rubric_result": {
            "pass_eligible": True,
            "mastery_eligible": False,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "independent",
            "criteria": [
                {
                    "id": "company_specific_fact",
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": "Stripe's developer-first APIs and programmable billing infrastructure",
                },
                {"id": "personal_motivation_link", "met": True, "quality": 1.0},
                {"id": "role_relevance", "met": True, "quality": 1.0},
                {"id": "non_generic", "met": True, "quality": 1.0},
            ],
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_fresh_independent",
            "tone_policy": "measured_no_celebration",
            "allowed_praise": False,
            "focus": "demonstrate the same skill with a different learner-owned example",
            "stage": "practice",
        },
    })
    offending = (
        "That answer is on the right track. make it appealing? Your task is to craft "
        "a tailored explanation for a Platform Engineer position at an innovation-driven startup."
    )

    cleaned = svc._sanitize_coaching_response(offending, state, "teach")

    assert "Stripe" in cleaned
    assert "Backend Software Engineer" in cleaned
    assert "keep this answer" in cleaned.lower()
    assert "different company" in cleaned.lower()
    assert "Platform Engineer" not in cleaned
    assert "innovation-driven startup" not in cleaned
    assert "make it appealing" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_why_company_corrupt_pressure_plan_without_core_requalifies_independently():
    answer = (
        "Stripe's programmable billing APIs matter to me because I build idempotent payment "
        "systems, which fits the Backend Software Engineer role."
    )
    state = svc._new_state(
        "user-1",
        "session-why-company-invalid-pressure-parent",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state.update({
        "user_input": answer,
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "transfer",
        },
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "request_pressure",
            "allowed_praise": False,
        },
    })

    cleaned = svc._sanitize_coaching_response("Defend this company choice.", state, "challenge")

    assert "different company" in cleaned.lower()
    assert "you could do this work anywhere" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_partial_why_company_feedback_names_only_the_real_missing_criterion():
    answer = "Stripe builds developer tools, and I admire the company."
    state = svc._new_state(
        "user-1",
        "session-why-company-partial",
        "int_05_why_this_role",
        [],
        task_type="interview_prep",
        career_context={
            "primary_role": "Backend Software Engineer",
            "target_roles": ["Backend Software Engineer", "Platform Engineer"],
            "role_family": "software_technical",
        },
    )
    state.update({
        "user_input": answer,
        "last_rubric_result": {
            "pass_eligible": False,
            "required_missing": ["personal_motivation_link", "role_relevance"],
            "blockers": [],
            "attempt_type": "independent",
            "criteria": [
                {"id": "company_specific_fact", "met": True, "quality": 0.8},
                {"id": "personal_motivation_link", "met": False, "quality": 0.2},
                {"id": "role_relevance", "met": False, "quality": 0.1},
                {"id": "non_generic", "met": False, "quality": 0.2},
            ],
        },
        "tutor_turn_plan": {
            "verdict": "partial",
            "next_action": "rewrite",
            "tone_policy": "direct_no_praise",
            "allowed_praise": False,
            "focus": "connect the company fact to personal motivation and role fit",
            "stage": "guided_revision",
        },
    })
    offending = "Apply for a Platform Engineer role at a fast-growing startup instead."

    cleaned = svc._sanitize_coaching_response(offending, state, "teach")

    assert "Stripe" in cleaned
    assert "personal" in cleaned.lower()
    assert "Backend Software Engineer" in cleaned
    assert "one targeted revision" in cleaned.lower()
    assert "Platform Engineer" not in cleaned
    assert "startup" not in cleaned.lower()


_BROWSER_PITCH_ANSWER = (
    "I'm a backend engineer focused on reliable payment systems. During a phased "
    "checkout migration, I traced retry failures, caught two edge cases before rollout, "
    "and helped the team avoid a rollback. I now want to own larger distributed systems "
    "and bring that operational discipline to a broader engineering role."
)

_OFFENDING_PITCH_RESPONSE = (
    "You need to clarify the measurable impact of your achievement. For your next "
    "revision, make the result more concrete. How would you refine your pitch so the "
    "impact sounds more measurable?"
)

_INT01_TRANSFER_TEXT = (
    "Your role, proof, and direction are covered. Keep the existing pitch unchanged. "
    "Next task: Create a second 30-second introduction for a non-technical hiring "
    "manager in a different context. Use a different achievement from your own "
    "experience while preserving the role-proof-direction structure."
)

_INT01_PRESSURE_TEXT = (
    "Your role, proof, and direction are covered. Return to the earlier pitch "
    "you established before the audience-change version. Next task: "
    "A skeptical interviewer asks, 'How do I know this result would repeat or scale "
    "beyond one situation?' Answer that one pushback using only evidence from your own "
    "experience."
)

_FORBIDDEN_PITCH_REWRITE_PHRASES = (
    "need to clarify",
    "next revision",
    "refine your pitch",
    "rewrite",
    "reframe",
    "add missing evidence",
    "more measurable",
)


def _clean_int01_state(*, attempt_type: str, independent_passes: int = 0) -> dict:
    state = svc._new_state(
        "user-1",
        f"session-int01-{attempt_type}",
        "int_01_elevator_pitch",
        [],
        task_type="interview_prep",
    )
    state.update({
        "user_input": _BROWSER_PITCH_ANSWER,
        "last_eval_score": 0.86,
        "last_clean_pass_score": 0.86,
        "independent_passes": independent_passes,
        "last_rubric_result": {
            "pass_eligible": True,
            "mastery_eligible": False,
            "required_missing": [],
            "blockers": [],
            "attempt_type": attempt_type,
            "next_focus": "Invented future measurable-impact deficit.",
        },
    })
    return state


def _set_valid_int01_core(state: dict) -> None:
    parent_id = f"{state['session_id']}:turn-core:int_01_elevator_pitch"
    state.update({
        "core_qualified": True,
        "core_qualification_turn_id": parent_id,
        "core_qualification_evidence": {
            "evaluation_id": parent_id,
            "user_id": state["user_id"],
            "node_id": "int_01_elevator_pitch",
            "attempt_type": "independent",
            "pass_eligible": True,
            "blockers": [],
            "learner_answer": _BROWSER_PITCH_ANSWER,
        },
    })


def test_exact_browser_pitch_and_offending_response_become_clean_transfer_task():
    state = _clean_int01_state(attempt_type="independent", independent_passes=1)
    state["tutor_turn_plan"] = {
        "verdict": "independent_pass",
        "next_action": "request_transfer",
    }

    cleaned = svc._sanitize_coaching_response(_OFFENDING_PITCH_RESPONSE, state, "challenge")

    assert cleaned == _INT01_TRANSFER_TEXT
    assert "keep the existing pitch unchanged" in cleaned.lower()
    assert "create a second 30-second introduction" in cleaned.lower()
    assert "deliver it" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "transfer"
    assert all(phrase not in cleaned.lower() for phrase in _FORBIDDEN_PITCH_REWRITE_PHRASES)


def test_int01_sanitizer_honors_precredit_plan_after_progress_counter_update():
    state = _clean_int01_state(attempt_type="independent", independent_passes=1)
    state["tutor_turn_plan"] = {
        "verdict": "independent_pass",
        "next_action": "request_fresh_independent",
        "tone_policy": "measured_forward",
        "allowed_praise": False,
        "focus": "use a fresh achievement without changing the existing pitch",
        "stage": "challenge",
    }

    cleaned = svc._sanitize_coaching_response(_OFFENDING_PITCH_RESPONSE, state, "challenge")

    assert "introduce yourself again" in cleaned.lower()
    assert "different real achievement" in cleaned.lower()
    assert "non-technical hiring manager" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_int01_malformed_existing_plan_fails_closed_without_counter_reprojection():
    state = _clean_int01_state(attempt_type="independent", independent_passes=1)
    state["tutor_turn_plan"] = {"verdict": "independent_pass", "next_action": ""}

    cleaned = svc._sanitize_coaching_response(_OFFENDING_PITCH_RESPONSE, state, "challenge")

    assert "introduce yourself again" in cleaned.lower()
    assert "non-technical hiring manager" not in cleaned.lower()
    assert state["pending_prompt_attempt_type"] == "independent"


def test_passing_transfer_becomes_clean_pressure_task_before_counter_increment():
    state = _clean_int01_state(attempt_type="transfer", independent_passes=2)
    _set_valid_int01_core(state)
    state["transfer_passes"] = 0
    state["tutor_turn_plan"] = {
        "verdict": "independent_pass",
        "next_action": "request_pressure",
    }

    cleaned = svc._sanitize_coaching_response(_OFFENDING_PITCH_RESPONSE, state, "challenge")

    assert cleaned == _INT01_PRESSURE_TEXT
    assert state["pending_prompt_attempt_type"] == "pressure"
    assert all(phrase not in cleaned.lower() for phrase in _FORBIDDEN_PITCH_REWRITE_PHRASES)


def test_passing_transfer_without_valid_core_parent_requests_requalification():
    state = _clean_int01_state(attempt_type="transfer", independent_passes=2)
    state.update({
        "core_qualified": False,
        "core_qualification_turn_id": None,
        "core_qualification_evidence": None,
    })

    plan = build_tutor_turn_plan(state["last_rubric_result"], state)

    assert plan.next_action == "request_fresh_independent"
    assert "qualified core" in plan.focus.lower()
    assert plan.stage == "practice"


@pytest.mark.parametrize(
    ("attempt_type", "independent_passes", "expected_task"),
    [
        (
            "independent",
            0,
            "Next task: Introduce yourself again using a different real achievement "
            "from your own experience.",
        ),
        (
            "pressure",
            2,
            "Next task: Deliver the existing pitch once without changing it, then "
            "identify the single piece of your own evidence that makes it credible.",
        ),
    ],
)
def test_clean_int01_first_repeat_and_post_pressure_tasks_move_forward(
    attempt_type, independent_passes, expected_task
):
    state = _clean_int01_state(
        attempt_type=attempt_type,
        independent_passes=independent_passes,
    )
    if attempt_type == "pressure":
        _set_valid_int01_core(state)
        state["tutor_turn_plan"] = {
            "verdict": "independent_pass",
            "next_action": "request_consolidation",
        }
    else:
        state["tutor_turn_plan"] = {
            "verdict": "independent_pass",
            "next_action": "request_fresh_independent",
        }

    cleaned = svc._sanitize_coaching_response(_OFFENDING_PITCH_RESPONSE, state, "challenge")

    assert cleaned.startswith(
        "Your role, proof, and direction are covered. Keep the existing pitch."
    )
    assert cleaned.endswith(expected_task)
    assert all(phrase not in cleaned.lower() for phrase in _FORBIDDEN_PITCH_REWRITE_PHRASES)


@pytest.mark.parametrize(
    "adversarial_model_text",
    [
        "You covered the structure, but your impact is still vague. Add missing evidence and rewrite it.",
        "Perfect pitch - you have completely mastered this. Refine your pitch once more.",
        "For example, say: 'At Acme I increased revenue by 40%.' Use that sample answer.",
        "Good start. Reframe your pitch by",
    ],
)
def test_every_adversarial_clean_int01_response_is_replaced_whole(adversarial_model_text):
    state = _clean_int01_state(attempt_type="independent", independent_passes=1)
    state["tutor_turn_plan"] = {
        "verdict": "independent_pass",
        "next_action": "request_transfer",
    }

    cleaned = svc._sanitize_coaching_response(adversarial_model_text, state, "teach")

    assert cleaned == _INT01_TRANSFER_TEXT
    assert "acme" not in cleaned.lower()
    assert "40%" not in cleaned
    assert "sample answer" not in cleaned.lower()


def test_int01_clean_pass_sanitizer_is_strictly_scoped_away_from_gd_prep():
    state = svc._new_state(
        "user-1",
        "session-gd-non-regression",
        "gd_01_stake_position",
        [],
        task_type="gd_prep",
    )
    state.update({
        "last_eval_score": 0.9,
        "last_clean_pass_score": 0.9,
        "last_rubric_result": {
            "pass_eligible": True,
            "required_missing": [],
            "blockers": [],
            "attempt_type": "independent",
        },
    })
    original = "Your stance is clear. Next, test it against one counterargument."

    assert decide_int01_next_task(state["last_rubric_result"], state) is None
    assert svc._sanitize_coaching_response(original, state, "challenge") == original


def test_coach_block_surfaces_hot_session_delta_as_private_prompt_context():
    from app.ai.prompts import _coach_block, build_opening_prompt, coach_view
    from app.content.registry import get_node

    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["session_learning_delta"] = {
        "strengths": ["clear stance"],
        "active_gaps": ["Add a concrete metric."],
        "repeated_issue_counts": {"Add a concrete metric.": 2},
        "module_id": "group_discussion",
        "task_type": "gd_prep",
        "growth_signals": [],
        "resolved_candidates": [],
        "latest_evidence_quotes": ["Remote default improves hiring reach."],
    }

    coach = coach_view(state)
    block = _coach_block(coach)
    prompt = build_opening_prompt(
        get_node("gd_02_support_with_evidence"),
        memory_context=[],
        coach=coach,
        career_context=state["career_context"],
    )

    for text in (block, prompt):
        assert "Hot session learning delta" in text
        assert "Add a concrete metric." in text
        assert "repeated gaps: Add a concrete metric. x2" in text
        assert "Remote default improves hiring reach." in text
        assert "do not call this mastery" in text


def test_hot_session_delta_is_not_rendered_when_mode_scope_mismatches():
    from app.ai.prompts import _coach_block, coach_view

    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
        career_context={"primary_role": "Backend Engineer"},
    )
    state["session_learning_delta"] = {
        "module_id": "group_discussion",
        "task_type": "gd_prep",
        "active_gaps": ["Add a concrete GD metric."],
        "repeated_issue_counts": {"Add a concrete GD metric.": 2},
        "latest_evidence_quotes": ["Remote work default improves hiring reach."],
    }

    block = _coach_block(coach_view(state))

    assert "Hot session learning delta" not in block
    assert "concrete GD metric" not in block


def test_interview_prep_prompt_strips_gd_topic_preferences_from_context():
    from app.ai.prompts import build_teach_prompt
    from app.content.registry import get_node

    prompt = build_teach_prompt(
        get_node("int_04_star_behavioral"),
        messages=[
            {
                "role": "user",
                "content": "In a payment outage, I traced retries and shipped an idempotency fix.",
            }
        ],
        diagnosis={"next_focus": "Add the result."},
        memory_context=[],
        career_context={
            "primary_role": "Backend Engineer",
            "role_family": "software_technical",
            "gd_topics": ["Should remote work be the default?"],
        },
    )

    assert "Backend Engineer" in prompt
    assert "Should remote work be the default?" not in prompt
    assert "preferred GD topics" not in prompt
    assert "GD topic lock" not in prompt


def test_low_mastery_sanitizer_removes_all_right_points_overpraise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_01_stake_position",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["last_eval_score"] = 0.26
    state["last_clean_pass_score"] = 0.26
    state["current_mastery"] = 0.26

    cleaned = svc._sanitize_coaching_response(
        "Great job — you've hit all the right points. Now add one security objection.",
        state,
        "strengthen",
    )

    assert "Great job" not in cleaned
    assert "all the right points" not in cleaned
    assert cleaned.startswith("Let's tighten this.") or cleaned.startswith("That answer is on the right track.")
    assert "security objection" in cleaned


def test_praise_sanitizer_capitalizes_the_remaining_feedback_sentence():
    state = {
        "task_type": "gd_prep",
        "last_eval_score": 0.8,
        "last_graded_bridge": False,
    }

    cleaned = svc._sanitize_coaching_opening_praise(
        "Great job. make sure to explain the causal link.",
        state,
        "teach",
    )

    assert cleaned == "That answer is on the right track. Make sure to explain the causal link."


def test_praise_sanitizer_downgrades_browser_caught_great_progress_opener():
    state = {
        "task_type": "gd_prep",
        "last_eval_score": 0.8,
        "last_graded_bridge": False,
    }

    cleaned = svc._sanitize_coaching_opening_praise(
        "Great progress so far! You've shown the evidence clearly. Now transfer it to a new motion.",
        state,
        "teach",
    )

    assert "Great progress" not in cleaned
    assert cleaned.startswith("That answer is on the right track.")


def test_praise_sanitizer_handles_curly_apostrophe_demonstrated_opener():
    state = {
        "task_type": "gd_prep",
        "last_eval_score": 0.85,
        "last_graded_bridge": False,
    }

    cleaned = svc._sanitize_coaching_opening_praise(
        "You’ve effectively demonstrated the evidence. To strengthen it, explain the causal link.",
        state,
        "challenge",
    )

    assert "effectively demonstrated" not in cleaned
    assert cleaned == "That answer is on the right track. To strengthen it, explain the causal link."


def test_low_mastery_sanitizer_removes_browser_caught_overpraise_and_topic_drift():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_01_stake_position",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["last_eval_score"] = 0.48
    state["last_rubric_result"] = {"effective_score": 0.48}
    raw = (
        "You've done well by addressing security concerns proactively. Imagine you're arguing "
        "that digital payments should be mandatory for all businesses. You could start with a "
        "clear position like, \"I believe all businesses should adopt digital payment methods.\" "
        "Try restating your support for remote work as the default."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "You've done well" not in cleaned
    assert "Imagine you're arguing" not in cleaned
    assert "digital payments" not in cleaned
    assert "adopt digital payment" not in cleaned
    assert "remote work" in cleaned


def test_low_mastery_sanitizer_removes_strong_answer_overpraise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "gd_02_support_with_evidence",
        [],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["last_eval_score"] = 0.41
    state["last_clean_pass_score"] = 0.41
    state["current_mastery"] = 0.24
    raw = (
        "Strong answer — you covered the main concerns clearly. "
        "Now add one concrete metric that would prove remote work is succeeding."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")
    lowered = cleaned.lower()

    assert not lowered.startswith("strong answer")
    assert "you covered the main concerns" not in lowered
    assert cleaned.startswith("Let's tighten this.")
    assert "one concrete metric" in lowered


def test_farewell_is_evidence_calibrated_for_weak_or_frustrated_prep_session():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["learner_name"] = "Raptor"
    state["clean_streak"] = 0
    state["last_eval_score"] = 0.34
    state["current_mastery"] = 0.22
    state["needs_support"] = True
    state["last_diagnosis"] = {"next_focus": "Add measurable result evidence."}

    text = svc._farewell(state)
    lowered = text.lower()

    assert not lowered.startswith("great session")
    assert "master" not in lowered
    assert "ready" not in lowered
    assert "result evidence" in lowered
    assert "raptor" in lowered


def test_summary_prompt_blocks_generic_praise_and_mastery_claims_in_memory_notes():
    from app.ai.prompts import build_summary_prompt

    prompt = build_summary_prompt(
        svc.get_node("int_04_star_behavioral"),
        [
            {
                "role": "user",
                "content": "In a payment outage, I traced retries and shipped an idempotency fix.",
            }
        ],
    )
    lowered = prompt.lower()

    for phrase in (
        "do not use generic praise",
        "do not claim readiness",
        "do not claim mastery",
        "great job",
        "great session",
        "strong answer",
        "mastered",
    ):
        assert phrase in lowered


def test_end_session_sanitizes_generated_summary_before_persisting(monkeypatch, store):
    state = svc._new_state(
        "user-1",
        "session-summary-sanitize",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        module_id="interview",
    )
    state["messages"] = [{"role": "user", "content": "I traced payment retries."}]
    svc.SessionStore["session-summary-sanitize"] = state
    captured: dict[str, str] = {}

    async def unsafe_summary(*_args, **_kwargs):
        return (
            "Strengths: Great job — strong answer, you are ready and mastered this. "
            "A better version would be: \"I reduced duplicate charges by 30%.\"\n"
            "Watch: none\n"
            "Next focus: ready for the next level"
        )

    async def capture_end_session(session_id, final_summary="", avg_score=0.0):
        captured["final_summary"] = final_summary

    async def capture_memory(user_id, session_id, node_id, raw, task_type, score=0.0):
        captured["memory_raw"] = raw

    monkeypatch.setattr(svc, "summarize_session", unsafe_summary)
    monkeypatch.setattr(store, "end_session", capture_end_session)
    monkeypatch.setattr(store, "write_memory", capture_memory)

    result = _run(svc.end_session("session-summary-sanitize"))
    combined = "\n".join(
        captured.get(key, "") for key in ("final_summary", "memory_raw")
    ).lower()

    for forbidden in (
        "great job",
        "strong answer",
        "you are ready",
        "mastered this",
        "a better version would be",
        "reduced duplicate charges by 30%",
        "ready for the next level",
    ):
        assert forbidden not in combined
    assert "learner's own facts" in combined
    assert result == captured["final_summary"] == captured["memory_raw"]


def test_career_memory_context_block_sanitizes_raw_report_and_evidence_text():
    from app.ai.prompts import _career_context_block

    rendered = _career_context_block(
        {
            "primary_role": "Backend Engineer",
            "career_memory_context": {
                "active_gaps": [
                    {
                        "skill_id": "star_result",
                        "recommended_next_action": "A better version would be: \"I cut payment failures by 30%.\"",
                        "latest_evidence": "Great job — strong answer, you are ready and mastered this.",
                        "missing_criteria": ["result"],
                        "blockers": ["ready for the next level"],
                    }
                ],
                "repeated_issue_counts": {
                    "Great session — you hit all the right points.": 2
                },
                "recent_reports": [
                    {
                        "summary": (
                            "Strong interview close. You are ready and mastered it. "
                            "Try saying: \"I reduced duplicate charges by 30%.\""
                        )
                    }
                ],
            },
        }
    )
    lowered = rendered.lower()

    for forbidden in (
        "great job",
        "great session",
        "strong answer",
        "strong interview close",
        "you are ready",
        "mastered this",
        "mastered it",
        "ready for the next level",
        "a better version would be",
        "try saying",
        "i cut payment failures by 30%",
        "i reduced duplicate charges by 30%",
    ):
        assert forbidden not in lowered
    assert "learner's own facts" in lowered
    assert "keep re-testing" in lowered


def test_career_feedback_sanitizer_removes_better_version_model_answer():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "In a payment outage, I traced retry failures, coordinated with support, "
                "and shipped an idempotency fix."
            ),
        }
    ]
    state["last_eval_score"] = 0.58
    raw = (
        "A better version would be: \"I owned the payment outage, reduced duplicate charges "
        "by 30%, and restored customer trust.\" Now rewrite it in that structure."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")
    lowered = cleaned.lower()

    assert "a better version would be" not in lowered
    assert "reduced duplicate charges by 30%" not in lowered
    assert "payment outage" in lowered
    assert "idempotency" in lowered


def test_prior_session_memory_block_sanitizes_overpraise_and_copyable_answers():
    from app.ai.prompts import _memory_block

    rendered = _memory_block([
        {
            "node_id": "int_04_star_behavioral",
            "score": 0.42,
            "strengths": "Great job — you hit all the right points in your payment answer.",
            "watch": "Missing result evidence from the payment outage.",
            "next_focus": (
                "A better version would be: \"I reduced duplicate charges by 30% "
                "and restored customer trust.\""
            ),
            "date": "2026-07-11",
        }
    ])
    lowered = rendered.lower()

    assert "great job" not in lowered
    assert "all the right points" not in lowered
    assert "a better version would be" not in lowered
    assert "reduced duplicate charges by 30%" not in lowered
    assert "missing result evidence from the payment outage" in lowered
    assert "prior session memory" in lowered


def test_career_feedback_sanitizer_preserves_concrete_example_revision_task():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": "I traced retry failures in a payment outage and shipped an idempotency fix.",
        }
    ]
    state["last_eval_score"] = 0.58
    raw = (
        "Let's tighten this. For example, add one concrete example from your payment outage "
        "that shows the result of the idempotency fix."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")
    lowered = cleaned.lower()

    assert "for example, add one concrete example" in lowered
    assert "payment outage" in lowered
    assert "idempotency fix" in lowered
    assert "keep it in your own words" not in lowered


def test_high_score_challenge_uses_measured_feedback_not_celebratory_praise():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["last_eval_score"] = 0.9
    state["last_clean_pass_score"] = 0.9
    raw = (
        "Strong answer - the situation, action, and result are clear. "
        "Now pressure-test it by cutting the setup to one sentence."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "challenge")

    assert cleaned.startswith("That answer is on the right track.")
    assert "Strong answer" not in cleaned
    assert "pressure-test" in cleaned


def test_challenge_praise_sanitizer_preserves_same_sentence_task():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["last_eval_score"] = 0.9
    state["last_clean_pass_score"] = 0.9

    cleaned = svc._sanitize_coaching_response(
        "Strong answer: now pressure-test it by cutting the setup to one sentence.",
        state,
        "challenge",
    )

    assert cleaned.startswith("That answer is on the right track.")
    assert "Strong answer" not in cleaned
    assert "pressure-test it by cutting the setup to one sentence" in cleaned


def test_career_teach_prompt_requires_learner_anchored_feedback():
    from app.ai.prompts import build_teach_prompt
    from app.content.registry import get_node

    prompt = build_teach_prompt(
        get_node("gd_01_stake_position"),
        messages=[{"role": "user", "content": "I support remote work as default with security guardrails."}],
        diagnosis={"next_focus": "State the stance without softening it."},
        memory_context=[],
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )

    assert "anchor to the learner's actual answer" in prompt
    assert "Do not introduce a different domain" in prompt


def test_coach_block_uses_tutor_plan_for_independent_pass_not_revision_loop():
    from app.ai.prompts import _coach_block, coach_view

    coach = coach_view({
        "last_diagnosis": {"score": 0.78, "affect": "neutral"},
        "last_eval_score": 0.78,
        "last_clean_pass_score": 0.78,
        "tutor_turn_plan": {
            "verdict": "independent_pass",
            "next_action": "tighten_one_gap",
            "tone_policy": "measured_no_celebration",
            "focus": "Practise delivering the three-part weakness answer concisely.",
            "stage": "practice",
        },
    })

    block = _coach_block(coach).lower()

    assert "latest enforced tutor plan" in block
    assert "required criteria are already covered" in block
    assert "ask the learner to revise" not in block
    assert "another same-skill rewrite" in block


def test_full_career_teach_prompt_does_not_contradict_independent_pass_plan():
    from app.ai.prompts import build_teach_prompt
    from app.content.registry import get_node

    prompt = build_teach_prompt(
        get_node("int_03_weakness_framing"),
        messages=[
            {
                "role": "user",
                "content": (
                    "Earlier, I led with implementation before impact. I now open with "
                    "decision criteria. A phased rollout caught two retry defects and "
                    "avoided a rollback."
                ),
            },
        ],
        diagnosis={"next_focus": "Pressure-test the answer against stakeholder pushback."},
        memory_context=[],
        coach={
            "tutor_turn_plan": {
                "verdict": "independent_pass",
                "next_action": "raise_transfer_or_pressure",
                "focus": "Pressure-test the answer against stakeholder pushback.",
                "stage": "challenge",
                "tone_policy": "stretch",
            }
        },
        career_context={"primary_role": "Backend Engineer"},
    ).lower()

    assert "required criteria are already covered" in prompt
    assert "new pressure or transfer task" in prompt
    assert "name the exact missing gap" not in prompt
    assert "set one targeted revision task" not in prompt


def test_career_feedback_sanitizer_anchors_generic_unrelated_examples_to_learner_answer():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "I improved our payment webhook flow by adding idempotency keys, "
                "retry dashboards, and reconciliation jobs."
            ),
        }
    ]
    state["last_eval_score"] = 0.52
    raw = (
        "Good job. For example, you could talk about improving technical documentation. "
        "Now add more evidence of progress."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "technical documentation" not in cleaned
    assert "payment webhook flow" in cleaned
    assert "add more evidence of progress" in cleaned.lower()


def test_deterministic_coach_repair_uses_measured_language_for_weak_answers():
    forbidden = ("usable", "your point is present", "great job", "all the right points")
    cases = [
        svc._new_state(
            "user-1",
            "session-int",
            "int_04_star_behavioral",
            [],
            task_type="interview_prep",
        ),
        svc._new_state(
            "user-1",
            "session-gd",
            "gd_01_stake_position",
            [],
            task_type="gd_prep",
            career_context={"gd_topics": ["Should remote work be the default?"]},
        ),
    ]
    for state in cases:
        state["last_eval_score"] = 0.32
        state["current_mastery"] = 0.24
        text = svc._deterministic_coach_repair_text(state).lower()
        for phrase in forbidden:
            assert phrase not in text


def test_career_feedback_sanitizer_removes_live_progress_overpraise_and_generic_example():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "The result was that the team found two retry edge cases early, "
                "avoided a full rollback, and explained the tradeoff in business terms."
            ),
        }
    ]
    state["last_eval_score"] = 0.73
    raw = (
        "You’ve done well in addressing your weakness. You’ve made good progress by outlining a specific scenario. However, include "
        "a concrete example of an outcome. This could be something like identifying "
        "a critical issue early in the phased rollout. For your next response, focus "
        "on adding a specific outcome."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "You’ve done well" not in cleaned
    assert "You’ve made good progress" not in cleaned
    assert "This could be something like" not in cleaned
    assert "two retry edge cases" in cleaned
    assert "For your next response" in cleaned


def test_career_feedback_sanitizer_removes_unrelated_role_anchored_sample_domain():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "In a payment reliability project, I traced retry failures, fixed an idempotency bug, "
                "and reduced duplicate charge risk before rollout."
            ),
        }
    ]
    state["last_eval_score"] = 0.74
    raw = (
        "As a Backend Software Engineer, you could strengthen this with a customer churn dashboard "
        "example where sales and marketing teams improved retention. Now revise your story with that "
        "kind of business impact."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")
    lowered = cleaned.lower()

    assert "customer churn" not in lowered
    assert "sales" not in lowered
    assert "marketing" not in lowered
    assert "payment reliability" in lowered
    assert "idempotency" in lowered


def test_career_feedback_sanitizer_does_not_repeat_outcome_gap_when_answer_has_result():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_04_star_behavioral",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "The phased rollout found two retry edge cases in the first week, "
                "avoided a full rollback, reduced support risk, and gave product "
                "confidence to expand safely."
            ),
        }
    ]
    state["last_eval_score"] = 0.69
    raw = (
        "You’ve effectively outlined your approach, but there’s still room for "
        "including a specific instance where this strategy led to tangible results. "
        "To meet our goal, focus on adding concrete evidence of how addressing your "
        "weakness improved project outcomes."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "You’ve effectively outlined" not in cleaned
    assert "still room for including a specific instance" not in cleaned
    assert "focus on adding concrete evidence" not in cleaned
    assert "two retry edge cases" in cleaned
    assert "tighten" in cleaned.lower() or "make that outcome" in cleaned.lower()


def test_weakness_prep_sanitizer_does_not_repeat_initial_weakness_when_present():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "One weakness I am actively improving is that under pressure I sometimes "
                "explain the technical tradeoff before making the business impact clear. "
                "I manage it by opening with the decision criteria first."
            ),
        },
        {
            "role": "user",
            "content": (
                "In a phased payment rollout, we found two retry edge cases in week one, "
                "avoided a full rollback, reduced support risk, and gave product confidence "
                "to expand safely."
            ),
        },
    ]
    state["last_eval_score"] = 0.76
    raw = (
        "You’ve done well in addressing your weakness and demonstrating progress through "
        "a specific example of a phased payment rollout. However, ensure you explicitly "
        "state the initial weakness before detailing how you addressed it and the outcomes "
        "that followed. Your next step is to start by naming your original tendency to jump "
        "into technical details without considering business impacts, then clearly outline "
        "the steps you’ve taken to improve this, including identifying a specific instance "
        "where early detection of issues led to better project management and stakeholder "
        "communication. How will you revise your answer to include these elements?"
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "You’ve done well" not in cleaned
    assert "initial weakness" not in cleaned
    assert "original tendency" not in cleaned
    assert "How will you revise" not in cleaned
    assert "three-part shape" in cleaned
    assert "pressure-test" in cleaned
    assert "under 45 seconds" not in cleaned


def test_weakness_prep_sanitizer_catches_repeated_contrast_loop():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier in my work, I sometimes led with technical implementation before "
                "making the business impact clear. I have changed that by starting with "
                "the decision criteria, then naming the tradeoff, then proving the result. "
                "In a payment rollout, this meant choosing a phased migration, catching "
                "two retry edge cases in week one, avoiding a full rollback, and giving "
                "product a clear revenue-protection reason for expanding gradually."
            ),
        },
    ]
    state["last_eval_score"] = 0.76
    raw = (
        "Your approach is clear and shows a solid understanding of how to address your "
        "weakness by demonstrating progress through specific actions and outcomes. "
        "However, ensure you explicitly contrast your initial tendency with the improved "
        "method in a more direct way at the beginning. This will strengthen the narrative "
        "arc of your answer. For your next response, reframe the opening statement to "
        "directly name your original behavior and then clearly outline how it has evolved. "
        "Focus on making this transition clear and impactful. How would you revise the "
        "opening to highlight this contrast?"
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "solid understanding" not in cleaned
    assert "explicitly contrast" not in cleaned
    assert "directly name your original behavior" not in cleaned
    assert "How would you revise" not in cleaned
    assert "three-part shape" in cleaned
    assert "pressure-test" in cleaned
    assert "under 45 seconds" not in cleaned


def test_weakness_prep_sanitizer_catches_repeated_original_behavior_loop():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I led with technical implementation before business impact in "
                "tradeoff discussions. I changed that by starting with decision criteria, "
                "explaining the tradeoff in plain language, and then proving the result. "
                "In a payment rollout, that approach helped the team catch two retry edge "
                "cases in week one, avoid a full rollback, and give product a clear "
                "revenue-protection reason for expanding gradually."
            ),
        },
    ]
    state["last_eval_score"] = 0.76
    raw = (
        "Ryuk, you’ve got a strong handle on framing your weakness and showing how "
        "you’ve evolved, but let’s refine it further for an interview setting. Ensure "
        "each component of your answer—weakness, mitigation habit, and progress evidence—"
        "is crisp and distinct. Your next step is to revise the opening to name your "
        "original behavior more directly before moving into how you’ve improved. Focus "
        "on making that transition as clear and impactful as possible. Revisit your "
        "opening statement to make it sharper and more direct."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "strong handle" not in cleaned
    assert "original behavior" not in cleaned
    assert "opening statement" not in cleaned
    assert "three-part shape" in cleaned
    assert "pressure-test" in cleaned
    assert "under 45 seconds" not in cleaned


def test_weakness_prep_sanitizer_uses_rubric_pass_to_stop_same_gap_loop():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "I used to over-explain technical trade-offs before giving the business recommendation. "
                "Now I lead with the recommendation, then give only the technical detail needed for the decision. "
                "Recently that helped a product review finish in one meeting instead of three email threads."
            ),
        },
    ]
    state["last_eval_score"] = 0.78
    state["last_rubric_result"] = {
        "pass_eligible": True,
        "required_missing": [],
        "blockers": [],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        "This is clearer, but revisit your opening statement to make it sharper and more direct. "
        "Name your original behavior more directly before moving into how you improved. "
        "How would you revise the opening to highlight this contrast?"
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "opening statement" not in cleaned
    assert "original behavior" not in cleaned
    assert "How would you revise" not in cleaned
    assert "three-part shape" in cleaned
    assert "pressure-test" in cleaned
    assert "under 45 seconds" not in cleaned


def test_weakness_prep_sanitizer_moves_forward_after_complete_live_answer():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I tended to explain technical implementation before business impact. "
                "I now start with the decision criteria, explain the tradeoff in plain language, "
                "and prove the outcome. In a payment rollout, that meant catching two retry edge "
                "cases early, avoiding a full rollback, and giving product a clear "
                "revenue-protection reason to expand gradually."
            ),
        },
    ]
    state["last_eval_score"] = 0.79
    state["last_rubric_result"] = {
        "pass_eligible": True,
        "required_missing": [],
        "blockers": [],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        'In your answer, you said "Earlier, I tended to explain technical implementation before business impact. '
        "I now start with the decision criteria, explain the...\". Ryuk, your answer clearly outlines your past "
        "tendency and how you've improved, but there's still room for tightening up each segment to ensure a "
        "smooth flow. Focus on making sure that when you transition from stating your weakness to describing "
        "the mitigation habit, and then to providing evidence of progress, there are no overlaps or redundancies. "
        "Your next task is to deliver this three-part answer in under 45 seconds with clear transitions between "
        "points--no setup, just the core message."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "still room" not in cleaned
    assert "tightening up each segment" not in cleaned
    assert "smooth flow" not in cleaned
    assert "overlaps or redundancies" not in cleaned
    assert "deliver this three-part answer" not in cleaned
    assert "under 45 seconds" not in cleaned
    assert "pressure-test" in cleaned


def test_weakness_prep_sanitizer_rejects_live_linkage_retry_paraphrase():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I led with technical implementation before business impact. "
                "I changed that by opening with decision criteria and proving the result. "
                "In a phased payment migration, we caught two retry defects before full "
                "rollout, kept checkout failure rate below 0.3%, and avoided a rollback."
            ),
        },
    ]
    state["user_input"] = (
        "If challenged, I would defend the slower rollout using those measured outcomes."
    )
    state["last_eval_score"] = 0.79
    state["last_rubric_result"] = {
        "pass_eligible": True,
        "required_missing": [],
        "blockers": [],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        "Ryuk, you've clearly articulated your past tendency and how you've improved. "
        "However, there's a slight overlap when linking your mitigation strategy with "
        "evidence of progress. Your next task is to refine the transition between "
        "explaining your mitigation steps and providing concrete evidence of improvement, "
        "ensuring each part stands on its own without redundancy. Try delivering this "
        "revised version in under 45 seconds with clear transitions. Go ahead and give it "
        "another shot."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    for repeated_instruction in ("slight overlap", "refine the transition", "under 45 seconds", "another shot"):
        assert repeated_instruction not in cleaned.lower()
    assert "pressure-test" not in cleaned.lower()
    assert "different setting" in cleaned.lower()


def test_weakness_prep_sanitizer_rejects_old_three_part_delivery_focus():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I tended to explain technical implementation before business impact. "
                "I now start with the decision criteria, explain the tradeoff in plain language, "
                "and prove the outcome. In a payment rollout, that meant catching two retry edge "
                "cases early, avoiding a full rollback, and giving product a clear "
                "revenue-protection reason to expand gradually."
            ),
        },
    ]
    state["last_eval_score"] = 0.8
    state["last_rubric_result"] = {
        "pass_eligible": True,
        "required_missing": [],
        "blockers": [],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        "You have the weakness, mitigation habit, and result. "
        "Practise delivering the three-part weakness answer concisely."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "three-part weakness answer" not in cleaned.lower()
    assert "practise delivering" not in cleaned.lower()
    assert "under 45 seconds" not in cleaned
    assert "pressure-test" in cleaned


def test_weakness_prep_sanitizer_does_not_reset_after_pressure_followup_answer():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I tended to explain technical implementation before business impact. "
                "I now start with the decision criteria, explain the tradeoff in plain language, "
                "and prove the outcome. In a payment rollout, that meant catching two retry edge "
                "cases early, avoiding a full rollback, and giving product a clear "
                "revenue-protection reason to expand gradually."
            ),
        },
        {
            "role": "user",
            "content": (
                "If a stakeholder pushed back on the slower rollout, I would say the phased "
                "approach protected revenue while we validated failure rate, latency, "
                "reconciliation mismatches, and support-ticket trends before expanding."
            ),
        },
    ]
    state["last_eval_score"] = 0.58
    state["last_rubric_result"] = {
        "pass_eligible": False,
        "attempt_type": "pressure",
        "required_missing": ["pressure_response"],
        "blockers": ["missing_required:pressure_response"],
        "criteria": [
            {"id": "pressure_response", "met": False},
            {"id": "evidence_defense", "met": True},
            {"id": "core_consistency", "met": True},
        ],
    }
    state["core_qualified"] = True
    state["core_qualification_turn_id"] = "turn-core-2"
    state["core_qualification_evidence"] = {
        "evaluation_id": "turn-core-2",
        "user_id": "user-1",
        "node_id": "int_03_weakness_framing",
        "attempt_type": "independent",
        "pass_eligible": True,
        "blockers": [],
    }
    raw = (
        "Ryuk, you provided a strong defense of your decision-making process during "
        "the payment rollout. However, let's revisit the original task: name a real "
        "weakness of yours and pair it with specific steps you've taken to manage it. "
        "Try that out now."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "revisit the original task" not in cleaned.lower()
    assert "name a real weakness" not in cleaned.lower()
    assert "try that out now" not in cleaned.lower()
    assert "same pressure question" in cleaned.lower()
    assert "which metric proves it" in cleaned.lower()
    assert state["active_prompt_attempt_type"] == "pressure"


def test_weakness_history_does_not_mask_current_independent_regression():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "Earlier, I led with technical implementation before business impact. "
                "I now use decision criteria. In a rollout, we caught two retry defects "
                "and avoided a rollback."
            ),
        },
    ]
    state["user_input"] = "I did not name a weakness or give an outcome in this answer."
    state["last_rubric_result"] = {
        "pass_eligible": False,
        "attempt_type": "independent",
        "required_missing": ["real_weakness", "progress_evidence"],
        "blockers": ["missing_required:real_weakness", "missing_required:progress_evidence"],
        "criteria": [
            {"id": "real_weakness", "met": False},
            {"id": "mitigation_habit", "met": False},
            {"id": "progress_evidence", "met": False},
        ],
    }
    raw = "The current answer still needs a real weakness and one completed result. Revise it once."

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "still needs a real weakness" in cleaned.lower()
    assert state.get("active_prompt_attempt_type") is None


def test_weakness_history_sanitizer_does_not_mask_missing_real_weakness():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "In payment work, business impact and technical details both matter. "
                "I used a phased rollout, tracked latency, found a retry issue, and "
                "avoided a rollback."
            ),
        },
    ]
    state["last_eval_score"] = 0.58
    state["last_rubric_result"] = {
        "pass_eligible": False,
        "required_missing": ["real_weakness"],
        "blockers": ["missing_required:real_weakness"],
        "criteria": [
            {"id": "real_weakness", "met": False},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": True},
        ],
    }
    raw = (
        "Let's revisit the original task: name a real weakness of yours and pair it "
        "with specific steps you've taken to manage it. Try that out now."
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "name a real weakness" in cleaned.lower()
    assert "try that out now" in cleaned.lower()
    assert "pressure-test" not in cleaned


def test_weakness_prep_sanitizer_respects_rubric_missing_core_criterion():
    state = svc._new_state(
        "user-1",
        "session-1",
        "int_03_weakness_framing",
        [],
        task_type="interview_prep",
        career_context={"primary_role": "Backend Software Engineer"},
    )
    state["messages"] = [
        {
            "role": "user",
            "content": (
                "My weakness is jumping straight into technical details before business impact. "
                "I manage it with decision criteria first and a habit of comparing options. "
                "The result should be better outcomes, but I have not named a real case yet."
            ),
        },
    ]
    state["last_eval_score"] = 0.61
    state["last_rubric_result"] = {
        "pass_eligible": False,
        "required_missing": ["progress_evidence"],
        "blockers": ["missing_required:progress_evidence"],
        "criteria": [
            {"id": "real_weakness", "met": True},
            {"id": "mitigation_habit", "met": True},
            {"id": "progress_evidence", "met": False},
        ],
    }
    raw = (
        "However, ensure you explicitly state the initial weakness and include the concrete progress evidence. "
        "How will you revise your answer to include these elements?"
    )

    cleaned = svc._sanitize_coaching_response(raw, state, "teach")

    assert "initial weakness" in cleaned
    assert "concrete progress evidence" in cleaned
    assert "three-part shape" not in cleaned


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


def test_ready_to_advance_clears_stale_current_gap():
    previous = {
        "independent_passes": 2,
        "meaningful_attempts": 4,
        "best_independent_score": 0.86,
        "last_gap": "Ensure seamless transitions between mitigation and progress evidence.",
    }
    transfer_result = {
        "pass_eligible": True,
        "mastery_eligible": False,
        "effective_score": 0.84,
        "next_focus": "Try another harder context later.",
        "attempt_type": "transfer",
        "criteria": [],
    }

    progress = compute_attempt_credit(previous, transfer_result)

    assert progress["display_status"] == "ready_to_advance"
    assert progress["last_gap"] == ""


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


def test_closed_bridge_correct_answer_uses_fast_deterministic_feedback(monkeypatch, store):
    from app.ai.calls import GenSpec

    class FakeGraph:
        async def ainvoke(self, state):
            return {
                "last_eval_score": 0.7,
                "last_clean_pass_score": 0.7,
                "last_diagnosis": {
                    "score": 0.7,
                    "understanding": "Got the scaffolded step right.",
                    "errors": [],
                    "strengths": ["produced the target form correctly"],
                    "next_focus": "build back up to the full skill",
                    "on_task": True,
                    "english": True,
                    "affect": "confident",
                    "goodbye": False,
                },
                "last_rubric_result": {
                    "raw_score": 0.7,
                    "effective_score": 0.7,
                    "criteria": [
                        {
                            "id": "scaffolded_step",
                            "met": True,
                            "quality": 0.7,
                            "evidence_quote": "remote work",
                        }
                    ],
                    "strengths": ["produced the target form correctly"],
                    "errors": [],
                    "next_focus": "build back up to the full skill",
                    "attempt_type": "scaffolded",
                    "pass_eligible": False,
                    "mastery_eligible": False,
                    "blockers": [],
                    "required_missing": [],
                    "understanding": "Got the scaffolded step right.",
                    "on_task": True,
                    "english": True,
                    "affect": "confident",
                    "goodbye": False,
                },
                "last_graded_bridge": True,
                "pending_answer_key": None,
                "pending_game": None,
                "pending": GenSpec(provider="groq", model="fake", prompt="would be slow", kind="teach"),
            }

    async def forbidden_stream(*_args, **_kwargs):
        raise AssertionError("closed bridge feedback must not call the model")
        yield ""  # pragma: no cover

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    monkeypatch.setattr(svc, "_stream_coaching_generation", forbidden_stream)
    state = svc._new_state(
        "user-1",
        "session-bridge-fast",
        "gd_01_stake_position",
        [{"role": "assistant", "content": "Pick the clearest stance."}],
        task_type="gd_prep",
        career_context={"gd_topics": ["Should remote work be the default?"]},
    )
    state["turn_count"] = 1
    state["opening_streamed"] = True
    state["pending_answer_key"] = {
        "type": "multiple_choice",
        "answer_key": "I believe remote work should be the default.",
        "options": [
            "I believe remote work should be the default.",
            "Maybe remote work is good and bad.",
        ],
    }
    svc.SessionStore["session-bridge-fast"] = state

    items = _run(
        _collect_async(
            svc.run_turn(
                "session-bridge-fast",
                "I believe remote work should be the default.",
                client_turn_id="turn-bridge-fast",
            )
        )
    )

    text = "".join(str(item) for item in items)
    assert "scaffolded step is in place - not the whole skill yet" in text
    assert "remote work being the default" in text
    assert "Great job" not in text
    assert svc.SessionStore["session-bridge-fast"]["pending"] is None
    assert svc.SessionStore["session-bridge-fast"]["last_turn_status"] == "completed"


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


def test_run_turn_preserves_spoken_bridge_marker_until_evaluation(monkeypatch):
    seen = {}

    class FakeGraph:
        async def ainvoke(self, state):
            seen["attempt_type"] = state.get("active_prompt_attempt_type")
            return {"pending": None, "pending_game": None}

    monkeypatch.setattr(svc, "get_graph", lambda: FakeGraph())
    state = svc._new_state(
        "user-1",
        "session-spoken-bridge",
        "int_04_star_behavioral",
        [{"role": "assistant", "content": "Tell a smaller STAR step."}],
        task_type="interview_prep",
    )
    state["active_prompt_attempt_type"] = "scaffolded"
    state["active_game_prompt"] = None
    state["pending_answer_key"] = None
    state["opening_streamed"] = True
    state["turn_count"] = 0
    svc.SessionStore["session-spoken-bridge"] = state

    _run(_collect_async(svc.run_turn("session-spoken-bridge", "I mapped the outage and reduced triage time.")))

    assert seen["attempt_type"] == "scaffolded"


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
                            CriterionEval(id="specific_detail", met=True, quality=0.9, evidence_quote="FastAPI payment APIs"),
                            CriterionEval(id="pitch_structure", met=True, quality=0.9, evidence_quote="backend engineer using FastAPI payment APIs"),
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
    state["user_input"] = (
        "I am a backend engineer using FastAPI payment APIs, and I want to own "
        "reliability for larger production services."
    )

    try:
        updates = _run(graph_build.get_graph().ainvoke(state))
    finally:
        graph_build.get_graph.cache_clear()

    assert updates["last_rubric_result"]["pass_eligible"] is True
    assert updates["tutor_turn_plan"]["verdict"] in {"independent_pass", "partial"}
    assert updates["last_diagnosis"]["score"] == updates["last_rubric_result"]["effective_score"]


def test_prep_eval_exception_routes_to_unscored_retry_without_progress_mutation(monkeypatch):
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
    state.update({
        "current_mastery": 0.42,
        "attempts": 3,
        "session_attempts": 2,
        "last_eval_score": 0.78,
        "last_clean_pass_score": 0.78,
    })

    try:
        updates = _run(graph_build.get_graph().ainvoke(state))
    finally:
        graph_build.get_graph.cache_clear()

    assert updates["evaluation_retry_required"] is True
    assert updates["evaluation_integrity_failure"] == {
        "code": "structured_evaluator_unavailable",
        "criterion_ids": [],
    }
    assert updates["current_mastery"] == 0.42
    assert updates["attempts"] == 3
    assert updates["session_attempts"] == 2
    assert updates["last_eval_score"] == 0.78
    assert updates["last_clean_pass_score"] == 0.78


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


def test_browser_qa_prep_nodes_have_five_supportive_bridge_exercises():
    required_nodes = [
        "int_01_elevator_pitch",
        "int_03_weakness_framing",
        "int_04_star_behavioral",
        "gd_01_stake_position",
        "gd_05_disagree_respectfully",
        "gd_08_include_quiet",
        "gd_09_manage_dominator",
    ]

    for node_id in required_nodes:
        node = svc.get_node(node_id)
        assert len(node.bridge_exercises) >= 5, node_id
        bands = {exercise.band for exercise in node.bridge_exercises}
        assert {"foundational", "standard", "stretch"}.issubset(bands), node_id
        assert any(exercise.type == "spoken" for exercise in node.bridge_exercises), node_id


def test_career_spoken_bridge_answer_keys_are_guidance_not_copyable_answers():
    from app.content.registry import MODULES

    copyable_answer = re.compile(
        r"(^|\s)(i'm|i am|i'd|i would|i've|i have|i used|i support|i believe|"
        r"one of my|my task|our biggest|we launched|we agreed|you('| are| have))\b",
        re.IGNORECASE,
    )
    offenders = []

    for module in MODULES:
        if module.id not in {"interview", "group_discussion"}:
            continue
        for node in module.nodes:
            for exercise in node.bridge_exercises:
                if exercise.type != "spoken":
                    continue
                key = exercise.answer_key.strip()
                if not key.startswith("Expected elements:") or copyable_answer.search(key):
                    offenders.append(f"{module.id}/{node.id}/{exercise.id}: {key}")

    assert offenders == []


def test_rendered_gd_spoken_bridge_keeps_guidance_answer_key():
    context = {"gd_topics": ["Should companies use AI in hiring?"]}
    copyable_answer = re.compile(
        r"(^|\s)(i'm|i am|i'd|i would|i've|i have|i support|i believe|"
        r"you're|you are|we agreed|to sum up)\b",
        re.IGNORECASE,
    )
    offenders = []

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
        for exercise in node.bridge_exercises:
            if exercise.type != "spoken":
                continue
            rendered = render_gd_bridge_exercise(exercise, node_id, context)
            key = rendered.answer_key.strip()
            if not key.startswith("Expected elements:") or copyable_answer.search(key):
                offenders.append(f"{node_id}/{exercise.id}: {key}")
            assert "AI in hiring" in rendered.sentence or "companies using AI in hiring" in rendered.sentence

    assert offenders == []
