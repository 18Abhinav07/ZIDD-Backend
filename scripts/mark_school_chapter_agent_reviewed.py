#!/usr/bin/env python3
"""Promote one validated School chapter after a bounded agent review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.content.school_rebuild_schema import LiveSchoolChapter


def mark_agent_reviewed(
    payload: dict[str, Any],
    *,
    reviewed_by: str,
    reviewed_at: str,
    review_evidence: list[str],
) -> dict[str, Any]:
    if not reviewed_by.strip() or not reviewed_at.strip():
        raise ValueError("school_agent_review_identity_required")
    evidence = [item.strip() for item in review_evidence if item.strip()]
    if not evidence:
        raise ValueError("school_agent_review_evidence_required")

    reviewed = dict(payload)
    reviewed.update(
        approval_status="agent_reviewed",
        reviewed_by=reviewed_by.strip(),
        reviewed_at=reviewed_at.strip(),
        review_evidence=evidence,
        runtime_sha256="0" * 64,
    )
    chapter = LiveSchoolChapter.model_validate(reviewed)
    reviewed["runtime_sha256"] = chapter.calculated_runtime_sha256()
    checked = LiveSchoolChapter.model_validate(reviewed)
    if checked.calculated_runtime_sha256() != reviewed["runtime_sha256"]:
        raise RuntimeError("school_agent_review_runtime_hash_unstable")
    return reviewed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=Path, required=True)
    parser.add_argument("--reviewed-by", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--review-evidence", action="append", required=True)
    args = parser.parse_args()

    payload = json.loads(args.chapter.read_text(encoding="utf-8"))
    reviewed = mark_agent_reviewed(
        payload,
        reviewed_by=args.reviewed_by,
        reviewed_at=args.reviewed_at,
        review_evidence=args.review_evidence,
    )
    args.chapter.write_text(
        json.dumps(reviewed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "chapter_id": reviewed["chapter_id"],
                "approval_status": reviewed["approval_status"],
                "runtime_sha256": reviewed["runtime_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
