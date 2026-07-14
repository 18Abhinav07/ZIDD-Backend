"""Print School V3 content counts for launch-readiness review."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content.school_v3_content import all_approved_chapters, validate_school_v3_launch_gate


def main() -> None:
    chapters = all_approved_chapters("english")
    by_class: dict[int, dict[str, int]] = defaultdict(lambda: {"chapters": 0, "items": 0, "chapter_checks": 0})
    for chapter in chapters:
        result = validate_school_v3_launch_gate(chapter)
        row = by_class[chapter.class_no]
        row["chapters"] += 1
        row["items"] += result.item_count
        row["chapter_checks"] += result.chapter_check_count
    for class_no in sorted(by_class):
        row = by_class[class_no]
        print(
            f"class={class_no} "
            f"chapters={row['chapters']} "
            f"items={row['items']} "
            f"chapter_checks={row['chapter_checks']}"
        )


if __name__ == "__main__":
    main()
