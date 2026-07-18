from types import SimpleNamespace

from app.content.school_rebuild_quality import (
    chapter_quality_issues,
    corpus_quality_issues,
)


def _activity(
    *,
    passage: str,
    prompt: str,
    teaching_block: str = "",
    options: list[str] | None = None,
    accepted_answers: list[str] | None = None,
    answer_rule: str | None = None,
    grading_mode: str | None = None,
    model_answer: str | None = None,
    min_response_words: int | None = None,
    concept_slots: list[SimpleNamespace] | None = None,
    evidence_role: str = "certifying",
):
    return SimpleNamespace(
        teaching_block=teaching_block,
        passage=passage,
        prompt=prompt,
        options=options or [],
        accepted_answers=accepted_answers or [],
        answer_rule=answer_rule,
        grading_mode=grading_mode,
        model_answer=model_answer,
        min_response_words=min_response_words,
        concept_slots=concept_slots,
        evidence_role=evidence_role,
    )


def test_quality_gate_rejects_internal_engine_labels_in_learner_copy():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    independent = chapter.levels[0].checks.independent_check
    independent.teaching_block = "Independent Check: explain the evidence."
    independent.passage = "Independent checkpoint context: Ravi finds a key."
    independent.prompt = "Misconception check: choose the required concept."

    issues = chapter_quality_issues(chapter)

    assert (
        "learner_copy_exposes_engine_label:eng_c5_ch01_level:"
        "independent_check:teaching_block:independent check:"
    ) in issues
    assert (
        "learner_copy_exposes_engine_label:eng_c5_ch01_level:"
        "independent_check:passage:independent checkpoint"
    ) in issues
    assert (
        "learner_copy_exposes_engine_label:eng_c5_ch01_level:"
        "independent_check:prompt:misconception check:"
    ) in issues

    independent.prompt = "Before certifying, explain the clue."
    issues = chapter_quality_issues(chapter)
    assert (
        "learner_copy_exposes_engine_label:eng_c5_ch01_level:"
        "independent_check:prompt:before certifying"
    ) in issues


def _chapter(*, chapter_id: str, prompt: str, assessment_passage: str):
    teaching_passage = "Mina checks the bicycle bell before she rides."
    checks = SimpleNamespace(
        guided_check=_activity(
            passage=teaching_passage,
            prompt=prompt,
            options=["Mina", "Ravi"],
            accepted_answers=["Mina"],
        ),
        bridge=_activity(
            passage="Ravi puts on his helmet near the gate.",
            prompt=f"Why does Ravi put on his helmet in {chapter_id}?",
            accepted_answers=["for safety", "to stay safe"],
        ),
        masterclass=_activity(
            passage="Asha presses the brake before the crossing.",
            prompt=f"What does Asha press in {chapter_id}?",
            accepted_answers=["the brake", "brake"],
        ),
        independent_check=_activity(
            passage="Neel rides only on the marked path.",
            prompt=f"Write one sentence about Neel's safe choice in {chapter_id}.",
            accepted_answers=[
                "Neel rides only on the marked path.",
                "Neel rides only on the marked path",
            ],
        ),
        transfer_check=_activity(
            passage="Tara waits for the green signal before walking.",
            prompt=f"How does Tara make a safe choice in {chapter_id}?",
            answer_rule="concept_slots",
        ),
    )
    level = SimpleNamespace(
        level_id=f"{chapter_id}_level",
        skill_ids=["writing.complete_sentence"],
        checks=checks,
    )
    item = SimpleNamespace(
        item_id=f"{chapter_id}_assessment_01",
        passage=assessment_passage,
        prompt="Who checks the bell?",
        skill_ids=["reading.sentence_comprehension"],
        options=["Mina", "Ravi"],
        accepted_answers=["Mina"],
        answer_rule=None,
    )
    return SimpleNamespace(
        chapter_id=chapter_id,
        levels=[level],
        chapter_assessment=SimpleNamespace(items=[item]),
    )


def test_quality_gate_rejects_reused_assessment_passage_and_brittle_writing_key():
    chapter = _chapter(
        chapter_id="eng_c2_ch01",
        prompt="Read the scene and choose the person.",
        assessment_passage="Mina checks the bicycle bell before she rides.",
    )

    issues = chapter_quality_issues(chapter)

    assert "assessment_reuses_teaching_passage:eng_c2_ch01_assessment_01" in issues
    assert (
        "brittle_constructed_exact_answer:eng_c2_ch01_level:independent_check"
        in issues
    )


def test_quality_gate_rejects_lightly_reworded_teaching_case_in_assessment():
    chapter = _chapter(
        chapter_id="eng_c3_ch03",
        prompt="Choose a fair action and explain why.",
        assessment_passage=(
            "Mira has spoken twice, Dev has not spoken, and the group promised "
            "equal turns."
        ),
    )
    chapter.levels[0].teaching_steps = [
        SimpleNamespace(
            phase="independent_application",
            activity=None,
            variant_pool=[
                _activity(
                    passage=(
                        "Mira speaks twice while Dev has not presented his sketch. "
                        "The group promised equal turns before beginning."
                    ),
                    prompt="Suggest a fair next step and support it with the card.",
                )
            ],
        )
    ]

    issues = chapter_quality_issues(chapter)

    assert (
        "assessment_near_reuses_teaching_passage:"
        "eng_c3_ch03_assessment_01"
    ) in issues


def test_quality_gate_allows_word_order_task_to_have_one_normalized_answer():
    chapter = _chapter(
        chapter_id="eng_c2_ch01",
        prompt="Read the scene and choose the person.",
        assessment_passage="A fresh assessment scene about a red bicycle.",
    )
    independent = chapter.levels[0].checks.independent_check
    chapter.levels[0].skill_ids = ["grammar.sentence_order"]
    independent.prompt = "Put the words in order to make a sentence."

    issues = chapter_quality_issues(chapter)

    assert not any(issue.startswith("brittle_constructed_exact_answer") for issue in issues)


def test_quality_gates_include_all_authored_revision_levels():
    shared_revision_prompt = "How should the rider respond at the busy crossing?"
    chapters = []
    for number in range(1, 5):
        revision_3_passage = f"Revision transfer passage {number}."
        chapter = _chapter(
            chapter_id=f"eng_c2_ch{number:02d}",
            prompt=f"Who is riding in chapter {number}?",
            assessment_passage=(
                revision_3_passage
                if number == 1
                else f"Fresh assessment passage {number}."
            ),
        )
        checks = chapter.levels[0].checks
        checks.revision_level_1 = _activity(
            passage=f"Revision support passage {number}.",
            prompt="Use the support steps to choose the safer action.",
            options=["wait", "run"],
            accepted_answers=["wait"],
        )
        checks.revision_level_2 = _activity(
            passage=f"Revision practice passage {number}.",
            prompt=f"Write the complete safety advice for rider {number}.",
            accepted_answers=["The rider waits before crossing the busy road."],
        )
        checks.revision_level_3 = _activity(
            passage=revision_3_passage,
            prompt=shared_revision_prompt,
            answer_rule="concept_slots",
        )
        chapters.append(chapter)

    chapter_issues = chapter_quality_issues(chapters[0])

    assert (
        "generic_prompt_frame:eng_c2_ch01_level:revision_level_1:use the support steps"
        in chapter_issues
    )
    assert (
        "brittle_constructed_exact_answer:eng_c2_ch01_level:revision_level_2"
        in chapter_issues
    )
    assert "assessment_reuses_teaching_passage:eng_c2_ch01_assessment_01" in chapter_issues
    assert (
        f"cross_chapter_prompt_template:{shared_revision_prompt}:4"
        in corpus_quality_issues(chapters)
    )


def test_corpus_gate_rejects_prompt_template_reused_across_many_chapters():
    chapters = [
        _chapter(
            chapter_id=f"eng_c2_ch{number:02d}",
            prompt="Find the clear clue in this scene. Who is riding?",
            assessment_passage=f"Fresh assessment passage {number}.",
        )
        for number in range(1, 5)
    ]

    issues = corpus_quality_issues(chapters)

    assert issues == (
        "cross_chapter_prompt_template:Find the clear clue in this scene. Who is riding?:4",
    )


def test_quality_gate_enforces_every_authored_variant_pool_depth():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    level = chapter.levels[0]
    level.teaching_steps = [
        SimpleNamespace(
            phase=phase,
            activity=None,
            variant_pool=[
                _activity(
                    passage=f"{phase} passage {index}.",
                    prompt=f"{phase} prompt {index}?",
                )
                for index in range(count)
            ],
        )
        for phase, count in (
            ("guided_practice", 3),
            ("independent_application", 3),
            ("transfer", 2),
            ("review", 1),
        )
    ]

    issues = chapter_quality_issues(chapter)

    assert "insufficient_teaching_variants:eng_c5_ch01_level:guided_practice:3:4" in issues
    assert (
        "insufficient_teaching_variants:eng_c5_ch01_level:independent_application:3:4"
        in issues
    )
    assert "insufficient_teaching_variants:eng_c5_ch01_level:transfer:2:4" in issues
    assert "insufficient_teaching_variants:eng_c5_ch01_level:review:1:4" in issues


def test_quality_gate_reserves_fresh_certifying_cases_after_support_recovery():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    level = chapter.levels[0]
    level.teaching_steps = [
        SimpleNamespace(
            phase=phase,
            activity=None,
            variant_pool=[
                _activity(
                    passage=f"{phase} recovery passage {index}.",
                    prompt=f"{phase} recovery prompt {index}?",
                )
                for index in range(count)
            ],
        )
        for phase, count in (
            ("guided_practice", 4),
            ("independent_application", 4),
            ("transfer", 3),
            ("review", 3),
        )
    ]

    issues = chapter_quality_issues(chapter)

    assert (
        "insufficient_teaching_variants:eng_c5_ch01_level:transfer:3:4"
        in issues
    )
    assert (
        "insufficient_teaching_variants:eng_c5_ch01_level:review:3:4"
        in issues
    )


def test_quality_gate_rejects_support_that_repeats_a_teaching_variant():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    level = chapter.levels[0]
    repeated_passage = level.checks.bridge.passage
    level.teaching_steps = [
        SimpleNamespace(
            phase="guided_practice",
            activity=None,
            variant_pool=[
                _activity(
                    passage=(
                        repeated_passage
                        if index == 0
                        else f"Fresh guided passage {index}."
                    ),
                    prompt=f"Guided prompt {index}?",
                )
                for index in range(4)
            ],
        )
    ]

    issues = chapter_quality_issues(chapter)

    assert "support_reuses_teaching_passage:eng_c5_ch01_level:bridge" in issues


def test_quality_gate_rejects_support_that_only_rewords_a_teaching_case():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    level = chapter.levels[0]
    level.checks.bridge.passage = (
        "Ravi packed the bright red bag beside the library door before lunch."
    )
    level.teaching_steps = [
        SimpleNamespace(
            phase="guided_practice",
            activity=None,
            variant_pool=[
                _activity(
                    passage=(
                        "Ravi packed a bright red bag beside the library door before lunch."
                        if index == 0
                        else f"Fresh guided passage number {index} with a new event."
                    ),
                    prompt=f"Guided prompt {index}?",
                )
                for index in range(4)
            ],
        )
    ]

    issues = chapter_quality_issues(chapter)

    assert "support_near_reuses_teaching_passage:eng_c5_ch01_level:bridge" in issues


def test_quality_gate_rejects_near_duplicate_certifying_variants():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    level = chapter.levels[0]
    level.teaching_steps = [
        SimpleNamespace(
            phase="independent_application",
            activity=None,
            variant_pool=[
                _activity(
                    passage=(
                        "Mina followed the long blue path towards the eastern school gate."
                        if index == 0
                        else f"Independent case {index} uses a completely different event and place."
                    ),
                    prompt=f"Independent prompt {index}?",
                )
                for index in range(4)
            ],
        ),
        SimpleNamespace(
            phase="transfer",
            activity=None,
            variant_pool=[
                _activity(
                    passage=(
                        "Mina followed a long blue path towards the eastern school gate."
                        if index == 0
                        else f"Transfer case {index} uses an unfamiliar situation and setting."
                    ),
                    prompt=f"Transfer prompt {index}?",
                )
                for index in range(3)
            ],
        ),
    ]

    issues = chapter_quality_issues(chapter)

    assert any(
        issue.startswith(
            "near_duplicate_teaching_case:eng_c5_ch01_level:"
            "independent_application:1:transfer:1"
        )
        for issue in issues
    )


def test_quality_gate_allows_parallel_cloze_drills_with_different_answers():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    level = chapter.levels[0]
    independent_passages = [
        "Complete the written word family: l_ght",
        "A gardener labels three seed trays before the rain begins.",
        "The museum guide points towards a newly restored clay pot.",
        "Two cousins compare bus routes on a colourful city map.",
    ]
    transfer_passages = [
        "Complete the written word family: n_ght",
        "A drummer listens for the conductor's final hand signal.",
        "The baker measures flour before warming the stone oven.",
    ]
    level.teaching_steps = [
        SimpleNamespace(
            phase="independent_application",
            activity=None,
            variant_pool=[
                _activity(
                    passage=independent_passages[index],
                    prompt=f"Independent prompt {index}?",
                    accepted_answers=["light" if index == 0 else f"answer-{index}"],
                    grading_mode="exact_text",
                )
                for index in range(4)
            ],
        ),
        SimpleNamespace(
            phase="transfer",
            activity=None,
            variant_pool=[
                _activity(
                    passage=transfer_passages[index],
                    prompt=f"Transfer prompt {index}?",
                    accepted_answers=["night" if index == 0 else f"transfer-{index}"],
                    grading_mode="exact_text",
                )
                for index in range(3)
            ],
        ),
    ]

    issues = chapter_quality_issues(chapter)

    assert not any(issue.startswith("near_duplicate_teaching_case") for issue in issues)


def test_quality_gate_rejects_strict_open_model_that_cannot_pass_itself():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    level = chapter.levels[0]
    level.checks.independent_check = _activity(
        passage="Ravi sees an empty nest after the storm.",
        prompt="Explain what Ravi infers and why.",
        grading_mode="strict_open_rubric",
        model_answer="The nest is empty.",
        min_response_words=8,
        concept_slots=[
            SimpleNamespace(id="inference", any_of=["birds flew away", "birds left"]),
            SimpleNamespace(id="evidence", any_of=["after the storm", "storm"]),
        ],
    )

    issues = chapter_quality_issues(chapter)

    assert (
        "strict_open_model_below_word_floor:eng_c5_ch01_level:independent_check:4:8"
        in issues
    )
    assert (
        "strict_open_model_missing_slot:eng_c5_ch01_level:independent_check:inference"
        in issues
    )
    assert (
        "strict_open_model_missing_slot:eng_c5_ch01_level:independent_check:evidence"
        in issues
    )


def test_quality_gate_rejects_certifying_strict_open_without_semantic_claim_slots():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    independent = chapter.levels[0].checks.independent_check
    independent.grading_mode = "strict_open_rubric"
    independent.model_answer = "The clue points to the correct place."
    independent.min_response_words = 6
    independent.concept_slots = []

    issues = chapter_quality_issues(chapter)

    assert (
        "strict_open_certifying_missing_concept_slots:"
        "eng_c5_ch01_level:independent_check"
        in issues
    )

    independent.evidence_role = "supported"
    assert not any(
        issue.startswith("strict_open_certifying_missing_concept_slots")
        for issue in chapter_quality_issues(chapter)
    )


def test_quality_gate_rejects_one_alias_shared_by_two_required_claims():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    chapter.levels[0].checks.independent_check = _activity(
        passage="Mina and Ravi carried a basket together.",
        prompt="Explain the action and its result.",
        grading_mode="strict_open_rubric",
        model_answer="Mina carried the basket with Ravi and reached the kitchen safely.",
        min_response_words=8,
        concept_slots=[
            SimpleNamespace(
                id="action",
                any_of=["carried the basket", "lifted the basket"],
            ),
            SimpleNamespace(
                id="result",
                any_of=["carried the basket", "reached the kitchen"],
            ),
        ],
    )

    issues = chapter_quality_issues(chapter)

    assert (
        "strict_open_alias_shared_across_slots:eng_c5_ch01_level:"
        "independent_check:carried the basket:action,result"
    ) in issues


def test_quality_gate_rejects_duplicate_assessment_tasks_across_forms():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    first = chapter.chapter_assessment.items[0]
    first.item_id = "eng_c5_ch01:form_a:01:reading"
    duplicate = SimpleNamespace(**vars(first))
    duplicate.item_id = "eng_c5_ch01:form_b:01:reading"
    chapter.chapter_assessment.items.append(duplicate)

    issues = chapter_quality_issues(chapter)

    assert (
        "duplicate_assessment_task:eng_c5_ch01:form_a:01:reading:"
        "eng_c5_ch01:form_b:01:reading"
    ) in issues


def test_quality_gate_rejects_relabelled_assessment_form_task():
    chapter = _chapter(
        chapter_id="eng_c5_ch01",
        prompt="Which clue matters?",
        assessment_passage="A fresh assessment passage.",
    )
    first = chapter.chapter_assessment.items[0]
    first.item_id = "eng_c5_ch01:form_a:01:reading"
    duplicate = SimpleNamespace(**vars(first))
    duplicate.item_id = "eng_c5_ch01:form_b:01:reading"
    duplicate.passage = "A fresh assessment passage about one bicycle."
    first.passage = "A fresh assessment passage about the bicycle."
    chapter.chapter_assessment.items.append(duplicate)

    issues = chapter_quality_issues(chapter)

    assert (
        "near_duplicate_assessment_task:eng_c5_ch01:form_a:01:reading:"
        "eng_c5_ch01:form_b:01:reading"
    ) in issues
