"""Generate School V3 seed content from the NCERT structural source map.

The generated content is original Zidd-authored exercise scaffolding. It uses
NCERT only for class/book/chapter ordering metadata and does not copy textbook
body text.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_ROOT = ROOT / "app" / "content"
SOURCE_MAP_ROOT = CONTENT_ROOT / "ncert_source_map" / "english"
BLUEPRINT_ROOT = CONTENT_ROOT / "school_v3_blueprints" / "english"
NCERT_URL = "https://ncert.nic.in/textbook.php"
CURRICULUM_VERSION = "school-v3-english-seed-2026-07"
REVIEWER = "zidd-seed-content-contract"
REVIEWED_AT = "2026-07-09"


BOOKS: dict[int, dict[str, object]] = {
    2: {"book_title": "Mridang", "book_code": "bemr1", "chapter_count": 13},
    3: {"book_title": "Santoor", "book_code": "cesa1", "chapter_count": 12},
    4: {"book_title": "Santoor", "book_code": "desa1", "chapter_count": 12},
    5: {"book_title": "Santoor", "book_code": "eesa1", "chapter_count": 10},
}

SKILLS_BY_CLASS: dict[int, tuple[str, ...]] = {
    2: (
        "reading.word_meaning_context",
        "reading.sentence_comprehension",
        "vocab.chapter_word_usage",
        "grammar.noun_verb_adjective",
        "writing.complete_sentence",
    ),
    3: (
        "reading.paragraph_main_idea",
        "reading.inference_reason",
        "grammar.tense_usage",
        "grammar.connectors_because_and_but",
        "writing.short_answer",
    ),
    4: (
        "reading.paragraph_main_idea",
        "reading.inference_reason",
        "vocab.chapter_word_usage",
        "writing.reason_answer",
        "writing.summary_own_words",
    ),
    5: (
        "reading.word_meaning_context",
        "reading.inference_reason",
        "grammar.connectors_because_and_but",
        "writing.reason_answer",
        "writing.summary_own_words",
    ),
}

SKILL_LABELS: dict[str, str] = {
    "reading.word_meaning_context": "word meaning from context",
    "reading.sentence_comprehension": "sentence meaning",
    "reading.paragraph_main_idea": "main idea",
    "reading.inference_reason": "reason inference",
    "vocab.chapter_word_usage": "chapter vocabulary use",
    "grammar.noun_verb_adjective": "noun verb adjective use",
    "grammar.tense_usage": "tense use",
    "grammar.connectors_because_and_but": "connectors",
    "writing.complete_sentence": "complete sentence writing",
    "writing.short_answer": "short answer writing",
    "writing.reason_answer": "reason answer writing",
    "writing.summary_own_words": "own words summary",
}

KEYS: tuple[str, ...] = ("garden", "river", "story", "morning", "festival")


def main() -> None:
    _write_source_maps()
    _write_blueprints()


def _write_source_maps() -> None:
    SOURCE_MAP_ROOT.mkdir(parents=True, exist_ok=True)
    for class_no, meta in BOOKS.items():
        book_code = str(meta["book_code"])
        chapter_count = int(meta["chapter_count"])
        chapters = [
            {
                "chapter_no": index,
                "chapter_id": _chapter_id(class_no, index),
                "chapter_title": f"{meta['book_title']} Chapter {index}",
                "selector_ref": f"{book_code}={index}-{chapter_count}",
                "selector_url": f"{NCERT_URL}?{book_code}={index}-{chapter_count}",
            }
            for index in range(1, chapter_count + 1)
        ]
        payload = {
            "subject_id": "english",
            "class_no": class_no,
            "book_title": meta["book_title"],
            "book_code": book_code,
            "chapter_count": chapter_count,
            "source_url": NCERT_URL,
            "structural_note": (
                "NCERT selector metadata only. Zidd stores original teaching "
                "content and does not copy textbook body text."
            ),
            "chapters": chapters,
        }
        _write_json(SOURCE_MAP_ROOT / f"class_{class_no}.json", payload)


def _write_blueprints() -> None:
    for class_no, meta in BOOKS.items():
        class_root = BLUEPRINT_ROOT / f"class_{class_no}"
        class_root.mkdir(parents=True, exist_ok=True)
        chapter_count = int(meta["chapter_count"])
        for chapter_no in range(1, chapter_count + 1):
            blueprint = _blueprint(class_no, meta, chapter_no, chapter_count)
            _write_json(class_root / f"{blueprint['chapter_id']}.json", blueprint)
        _write_review_status(class_root, class_no, chapter_count)


def _blueprint(
    class_no: int,
    meta: dict[str, object],
    chapter_no: int,
    chapter_count: int,
) -> dict[str, object]:
    chapter_id = _chapter_id(class_no, chapter_no)
    chapter_title = f"{meta['book_title']} Chapter {chapter_no}"
    return {
        "subject_id": "english",
        "class_no": class_no,
        "book_title": meta["book_title"],
        "curriculum_version": CURRICULUM_VERSION,
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "source_url": f"{NCERT_URL}?{meta['book_code']}={chapter_no}-{chapter_count}",
        "approval_status": "seed",
        "reviewed_by": REVIEWER,
        "reviewed_at": REVIEWED_AT,
        "outcomes": [
            _outcome(class_no, chapter_no, chapter_id, chapter_title, index, skill_id)
            for index, skill_id in enumerate(SKILLS_BY_CLASS[class_no], start=1)
        ],
    }


def _outcome(
    class_no: int,
    chapter_no: int,
    chapter_id: str,
    chapter_title: str,
    outcome_no: int,
    skill_id: str,
) -> dict[str, object]:
    label = SKILL_LABELS[skill_id]
    outcome_id = f"{chapter_id}_outcome_{outcome_no}"
    return {
        "outcome_id": outcome_id,
        "title": f"Build {label}",
        "skill_ids": [skill_id],
        "items": _items(
            class_no=class_no,
            chapter_no=chapter_no,
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            outcome_no=outcome_no,
            skill_id=skill_id,
            label=label,
        ),
    }


def _items(
    *,
    class_no: int,
    chapter_no: int,
    chapter_id: str,
    chapter_title: str,
    outcome_no: int,
    skill_id: str,
    label: str,
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    prefix = f"{chapter_id}_o{outcome_no}"
    answer_word = KEYS[(chapter_no + outcome_no) % len(KEYS)]

    for index in range(1, 7):
        items.append(
            _short_item(
                f"{prefix}_guided_{index}",
                "guided",
                skill_id,
                (
                    f"In {chapter_title}, use the sample sentence to practise "
                    f"{label}. Write one clear answer with a useful clue."
                ),
                answer_word,
                "Use the clue, name the idea, and answer in a complete sentence.",
            )
        )

    for index in range(1, 5):
        items.append(
            {
                "item_id": f"{prefix}_bridge_{index}",
                "stage": "bridge",
                "item_type": "multiple_choice",
                "prompt": (
                    f"Bridge support for {label}: which option best helps answer "
                    f"a question from {chapter_title}?"
                ),
                "skill_ids": [skill_id],
                "answer_key": "sentence clue",
                "options": ["sentence clue", "random guess", "longest word", "page number"],
            }
        )

    for index in range(1, 7):
        if index % 2 == 0:
            items.append(
                {
                    "item_id": f"{prefix}_independent_{index}",
                    "stage": "independent_check",
                    "item_type": "fill_blank",
                    "prompt": (
                        f"Complete the answer for {chapter_title}: I know this "
                        f"from the sentence __."
                    ),
                    "skill_ids": [skill_id],
                    "answer_key": "clue",
                }
            )
        else:
            items.append(
                _short_item(
                    f"{prefix}_independent_{index}",
                    "independent_check",
                    skill_id,
                    (
                        f"Answer independently for {chapter_title}. Give one "
                        f"clear {label} answer with your own clue."
                    ),
                    answer_word,
                    "The answer is clear, relevant, and written without a hint.",
                )
            )

    for index in range(1, 4):
        items.append(
            _short_item(
                f"{prefix}_transfer_{index}",
                "transfer_check",
                skill_id,
                (
                    f"Transfer {label} to a new classroom example. Write one "
                    f"sentence that shows the same idea."
                ),
                answer_word,
                "The same skill is used in a new context.",
            )
        )

    for index in range(1, 5):
        items.append(
            {
                "item_id": f"{prefix}_chapter_{index}",
                "stage": "chapter_check",
                "item_type": "multiple_choice",
                "prompt": (
                    f"Chapter check {index} for Class {class_no}, Chapter {chapter_no}: "
                    f"which choice best supports {label}?"
                ),
                "skill_ids": [skill_id],
                "answer_key": "clear reason",
                "options": ["clear reason", "copied line", "unrelated word", "empty answer"],
            }
        )

    return items


def _short_item(
    item_id: str,
    stage: str,
    skill_id: str,
    prompt: str,
    answer_key: str,
    model_answer: str,
) -> dict[str, object]:
    return {
        "item_id": item_id,
        "stage": stage,
        "item_type": "short_answer",
        "prompt": prompt,
        "skill_ids": [skill_id],
        "answer_key": answer_key,
        "model_answer": model_answer,
        "rubric": {
            "criteria": [
                "answers the actual prompt",
                "uses a relevant clue or reason",
                "writes in a complete sentence",
            ]
        },
    }


def _chapter_id(class_no: int, chapter_no: int) -> str:
    return f"eng_c{class_no}_ch{chapter_no:02d}"


def _write_review_status(class_root: Path, class_no: int, chapter_count: int) -> None:
    lines = [
        "# School V3 English Review Status",
        "",
        "Generated seed content for engine validation. Human pedagogical review is required before production marketing claims or APP_ENV=prod serving.",
        "",
        "| chapter_id | status | reviewer | reviewed_at |",
        "| --- | --- | --- | --- |",
    ]
    for chapter_no in range(1, chapter_count + 1):
        lines.append(f"| {_chapter_id(class_no, chapter_no)} | seed | {REVIEWER} | {REVIEWED_AT} |")
    (class_root / "REVIEW_STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
