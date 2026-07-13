from types import SimpleNamespace

from app.content.school_rebuild_quality import (
    chapter_quality_issues,
    corpus_quality_issues,
)


def _activity(
    *,
    passage: str,
    prompt: str,
    options: list[str] | None = None,
    accepted_answers: list[str] | None = None,
    answer_rule: str | None = None,
):
    return SimpleNamespace(
        passage=passage,
        prompt=prompt,
        options=options or [],
        accepted_answers=accepted_answers or [],
        answer_rule=answer_rule,
    )


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
