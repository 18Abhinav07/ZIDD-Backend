"""Audit live School chapters for structural and pedagogy-quality defects."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content.school_rebuild_content import LIVE_CHAPTER_ROOT, load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues, corpus_quality_issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--class", dest="class_no", type=int, choices=(2, 3, 4, 5))
    args = parser.parse_args()

    root = LIVE_CHAPTER_ROOT / "english"
    paths = sorted(
        (root / f"class_{args.class_no}").glob("*.json")
        if args.class_no
        else root.glob("class_*/*.json")
    )
    chapters = []
    issue_count = 0
    for path in paths:
        chapter = load_live_chapter_file(path)
        chapters.append(chapter)
        issues = list(chapter_quality_issues(chapter))
        if not 5 <= len(chapter.levels) <= 7:
            issues.append(f"launch_level_count:{len(chapter.levels)}")
        if chapter.chapter_assessment is None:
            issues.append("launch_chapter_assessment_missing")
        for level in chapter.levels:
            if level.checks.transfer_check is None:
                issues.append(f"launch_transfer_check_missing:{level.level_id}")
        if issues:
            issue_count += len(issues)
            for issue in issues:
                print(f"{chapter.chapter_id}: {issue}")

    corpus_issues = corpus_quality_issues(chapters)
    issue_count += len(corpus_issues)
    for issue in corpus_issues:
        print(f"corpus: {issue}")

    if issue_count:
        print(f"school_rebuild_content_failed chapters={len(chapters)} issues={issue_count}")
        return 1
    print(f"school_rebuild_content_ok chapters={len(chapters)} issues=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
