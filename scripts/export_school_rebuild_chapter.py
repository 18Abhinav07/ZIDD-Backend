"""Mechanically migrate one reviewed runtime chapter into the live JSON contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content.school_rebuild_content import LIVE_CHAPTER_ROOT
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services import school_rebuild_curriculum as curriculum


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", default="english")
    parser.add_argument("--class-no", type=int, required=True)
    parser.add_argument("--chapter-id", required=True)
    parser.add_argument("--reviewed-by", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--review-evidence", action="append", required=True)
    args = parser.parse_args()

    chapter = next(
        (
            candidate
            for candidate in curriculum._available_chapters(args.subject, args.class_no)
            if candidate.get("chapter_id") == args.chapter_id
        ),
        None,
    )
    if chapter is None:
        raise SystemExit(f"chapter_not_live:{args.chapter_id}")
    canonical_runtime = json.dumps(
        chapter,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    payload = {
        "approval_status": "qa_approved",
        "reviewed_by": args.reviewed_by,
        "reviewed_at": args.reviewed_at,
        "review_evidence": args.review_evidence,
        "runtime_sha256": hashlib.sha256(canonical_runtime).hexdigest(),
        **chapter,
    }
    validated = LiveSchoolChapter.model_validate(payload)
    destination = (
        LIVE_CHAPTER_ROOT
        / args.subject
        / f"class_{args.class_no}"
        / f"{args.chapter_id}.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            validated.model_dump(exclude_none=True, exclude_unset=True),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(destination)


if __name__ == "__main__":
    main()
