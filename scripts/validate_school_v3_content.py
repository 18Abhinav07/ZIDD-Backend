"""Validate all approved School V3 content files."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content.school_v3_content import all_approved_chapters, validate_school_v3_launch_gate


def main() -> None:
    chapters = all_approved_chapters("english")
    total_items = 0
    total_chapter_checks = 0
    for chapter in chapters:
        result = validate_school_v3_launch_gate(chapter)
        total_items += result.item_count
        total_chapter_checks += result.chapter_check_count
    print(
        "school_v3_content_ok "
        f"chapters={len(chapters)} "
        f"items={total_items} "
        f"chapter_checks={total_chapter_checks}"
    )


if __name__ == "__main__":
    main()
